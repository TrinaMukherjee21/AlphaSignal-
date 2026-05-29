import os
import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

class SentimentModel:
    def __init__(self, model_name="ProsusAI/finbert"):
        self.lite_mode = os.getenv("LITE_MODE", "false").lower() == "true"
        self.vader = SentimentIntensityAnalyzer()
        self.batch_size = 16
        
        if self.lite_mode:
            logger.info("🚀 [NLP] LITE_MODE enabled. Using VADER for all sentiment scores (High performance, Low RAM).")
            self.model = None
            self.tokenizer = None
            self.device = "cpu"
        else:
            try:
                import torch
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                import torch.nn.functional as F
                self.torch_f = F
                
                logger.info(f"🧠 [NLP] Loading heavy FinBERT model ({model_name})...")
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
            except Exception as e:
                logger.error(f"❌ [NLP] Failed to load heavy model: {e}. Falling back to LITE_MODE.")
                self.lite_mode = True
                self.model = None

    def score_batch(self, texts: list[str]) -> list[float]:
        if self.lite_mode:
            return [self.vader.polarity_scores(t)['compound'] for t in texts]

        scores = []
        texts_to_bert = []
        bert_indices = []

        for i, text in enumerate(texts):
            word_count = len(text.split())
            if word_count < 20:
                # Use VADER fallback
                vader_score = self.vader.polarity_scores(text)['compound']
                scores.append(vader_score)
            else:
                # Mark for BERT processing
                texts_to_bert.append(text)
                bert_indices.append(i)
                scores.append(0.0)  # Placeholder

        # Process BERT batch
        if texts_to_bert and self.model:
            import torch
            for i in range(0, len(texts_to_bert), self.batch_size):
                batch_texts = texts_to_bert[i:i + self.batch_size]
                batch_indices = bert_indices[i:i + self.batch_size]
                
                inputs = self.tokenizer(batch_texts, padding=True, truncation=True, return_tensors="pt").to(self.device)
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    probs = self.torch_f.softmax(outputs.logits, dim=-1)
                    
                    # FinBERT labels: 0: positive, 1: negative, 2: neutral
                    # Score = pos_prob - neg_prob
                    batch_scores = (probs[:, 0] - probs[:, 1]).cpu().tolist()
                    
                    for idx, score in zip(batch_indices, batch_scores):
                        scores[idx] = score
        else:
            # Fallback if bert is skipped
            for idx in bert_indices:
                scores[idx] = self.vader.polarity_scores(texts[idx])['compound']

        return scores
