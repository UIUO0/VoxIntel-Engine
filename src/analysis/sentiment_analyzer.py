from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Initialize the analyzer once to avoid reloading overhead
analyzer = SentimentIntensityAnalyzer()

def get_score(text):
    """
    Analyzes the sentiment of the given text using VADER.
    
    Args:
        text (str): The text to analyze.
        
    Returns:
        float: The compound sentiment score between -1.0 (most negative) and 1.0 (most positive).
    """
    if not text or not isinstance(text, str):
        return 0.0
        
    scores = analyzer.polarity_scores(text)
    return scores['compound']
