import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SystemLauncher")

_lite = os.getenv("LITE_MODE", "false").lower() == "true"
if _lite:
    logger.info("✨ [System] Booting up in LITE_MODE (VADER sentiment only, low memory).")
else:
    logger.info("✨ [System] Booting up... Loading heavy ML libraries (Transformers/PyTorch).")
    logger.warning("⏳ [WAIT] This specific import can take up to 2-4 minutes on Windows during metadata scans. Please do not cancel!")


import asyncio
import uvicorn
import signal
from api.main import app
from nlp.worker import NLPWorker
from scrapers.main import main as scraper_main
from db.price_processor import PriceProcessor

async def run_api():
    """Starts the FastAPI server via Uvicorn."""
    import os
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"🚀 [API] Starting on http://0.0.0.0:{port}")
    config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=port, 
        log_level="info",
        access_log=False
    )
    server = uvicorn.Server(config)
    await server.serve()

async def run_worker():
    """Starts the NLP Worker coroutine."""
    logger.info("🧠 [NLP] Starting Worker...")
    worker = NLPWorker()
    try:
        await worker.start()
    except asyncio.CancelledError:
        logger.info("🧠 [NLP] Worker cancelled, cleaning up...")
        await worker.producer.stop()
        await worker.consumer.stop()
        raise

async def run_scrapers():
    """Starts the Scrapers main coroutine."""
    logger.info("🕷️ [Scrapers] Starting Scrapers...")
    try:
        await scraper_main()
    except asyncio.CancelledError:
        logger.info("🕷️ [Scrapers] Scrapers cancelled.")
        raise

async def run_price_processor():
    """Starts the Price Processor coroutine."""
    logger.info("📈 [Prices] Starting Price Processor...")
    processor = PriceProcessor()
    try:
        await processor.start()
    except asyncio.CancelledError:
        logger.info("📈 [Prices] Price Processor cancelled.")
        raise

async def main():
    """Coordinator to run all services concurrently."""
    # Define the tasks
    tasks = [
        run_api(),
        run_worker(),
        run_scrapers(),
        run_price_processor()
    ]
    
    try:
        # Run everything together
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        # This is expected when the loop is stopped
        pass
    except Exception as e:
        logger.error(f"💥 [System] A service encountered a fatal error: {e}")
        raise

if __name__ == "__main__":
    logger.info("✨ Initializing Trade Sentiment Dashboard Services...")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 [System] KeyboardInterrupt received. Shutting down all services...")
    except Exception as e:
        logger.error(f"💥 [System] Unexpected system failure: {e}")
