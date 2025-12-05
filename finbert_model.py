import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

# --- Configuration ---
FINBERT_MODEL_NAME = "ProsusAI/finbert"
DECISION_MAPPING = {0: "SELL", 1: "HOLD", 2: "BUY"}
THRESHOLD_BUY = 0.6  # Confidence threshold for a definitive BUY
THRESHOLD_SELL = 0.6 # Confidence threshold for a definitive SELL

class StockActionAgent:
    """
    Core AI Agent that processes news and makes a stock action decision.
    """
    def __init__(self):
        # Load pre-trained FinBERT model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(FINBERT_MODEL_NAME)
        self.model = AutoModelForSequenceClassification.from_pretrained(FINBERT_MODEL_NAME)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()

    def _get_sentiment(self, news_text: str):
        """
        Analyzes the sentiment of a news article using FinBERT.
        Returns the probabilities for Negative, Neutral, Positive.
        """
        inputs = self.tokenizer(news_text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        inputs.to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)

        # Get probabilities from logits (softmax)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1).squeeze().cpu().numpy()
        # The default FinBERT output order is: Negative, Neutral, Positive (0, 1, 2)
        return probs # [Prob_Negative, Prob_Neutral, Prob_Positive]

    def make_decision(self, news_items: list):
        """
        Processes a list of news items and generates a consolidated decision.
        (This is a simplified RL/Event Extraction simulation)
        """
        if not news_items:
            return {"action": "HOLD", "reasoning": "No relevant news found for today."}

        all_probs = []
        for item in news_items:
            probs = self._get_sentiment(item['snippet'])
            all_probs.append(probs)

        # 1. Aggregate Sentiment (Simple Averaging)
        avg_probs = np.mean(all_probs, axis=0)
        neg_p, neut_p, pos_p = avg_probs

        # 2. Decision Logic (Simplified Rule-Based "RL Agent" simulation)
        if pos_p >= THRESHOLD_BUY and pos_p > neg_p:
            action = "BUY"
            reasoning = f"Strong **Positive Sentiment** (Prob: {pos_p:.2f}) observed across multiple articles, suggesting potential upside. Key drivers include positive earnings news and market expansion."
        elif neg_p >= THRESHOLD_SELL and neg_p > pos_p:
            action = "SELL"
            reasoning = f"Significant **Negative Sentiment** (Prob: {neg_p:.2f}) detected, likely due to regulatory concerns or missed revenue targets. Caution is advised."
        else:
            action = "HOLD"
            reasoning = f"The sentiment is **Neutral/Mixed**. Positive ({pos_p:.2f}) and Negative ({neg_p:.2f}) factors are balanced. Awaiting clearer market signals or stronger events before taking action."

        # 3. Simulated Event Extraction
        # In a real system, you'd use a separate model to tag events like 'Acquisition', 'Layoff', 'Earnings Miss'.
        # For this example, we'll simulate a key event based on sentiment.
        if action == "BUY":
             key_event = "Positive Earnings Report and Future Guidance"
        elif action == "SELL":
             key_event = "Regulatory Investigation Announced"
        else:
             key_event = "General Market Volatility"


        return {
            "action": action,
            "sentiment_score": {"Positive": f"{pos_p:.4f}", "Negative": f"{neg_p:.4f}", "Neutral": f"{neut_p:.4f}"},
            "reasoning": reasoning,
            "key_event": key_event,
            "news_count": len(news_items),
            "timestamp": "2025-12-05 10:00:00 UTC" # Use a real timestamp in the final version
        }
