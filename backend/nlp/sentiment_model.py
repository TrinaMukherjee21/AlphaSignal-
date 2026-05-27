import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import torch.nn.functional as F

class SentimentModel:
    def __init__(self, model_name="ProsusAI/finbert"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
        self.vader = SentimentIntensityAnalyzer()
        self.batch_size = 16

    def score_batch(self, texts: list[str]) -> list[float]:
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
        if texts_to_bert:
            for i in range(0, len(texts_to_bert), self.batch_size):
                batch_texts = texts_to_bert[i:i + self.batch_size]
                batch_indices = bert_indices[i:i + self.batch_size]
                
                inputs = self.tokenizer(batch_texts, padding=True, truncation=True, return_tensors="pt").to(self.device)
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    probs = F.softmax(outputs.logits, dim=-1)
                    
                    # FinBERT labels: 0: positive, 1: negative, 2: neutral
                    # Score = pos_prob - neg_prob
                    batch_scores = (probs[:, 0] - probs[:, 1]).cpu().tolist()
                    
                    for idx, score in zip(batch_indices, batch_scores):
                        scores[idx] = score

        return scores
