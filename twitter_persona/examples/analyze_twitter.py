import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Add the parent directory to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from twitter_persona.src.database.database import TwitterDatabase
from twitter_persona.src.fetcher.twitter_fetcher import TwitterFetcher
from twitter_persona.src.analyzer.tweet_analyzer import TweetAnalyzer

def main():
    # Load environment variables
    load_dotenv()
    
    # Verify required API keys
    if "TWITTER_BEARER_TOKEN" not in os.environ:
        raise ValueError("TWITTER_BEARER_TOKEN not found in environment variables")
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    # Initialize components
    db = TwitterDatabase()
    fetcher = TwitterFetcher()
    analyzer = TweetAnalyzer()
    
    # Get username from user input
    username = input("Enter Twitter username to analyze (without @): ")
    
    print(f"\nFetching tweets for @{username}...")
    
    # Fetch recent activity (last 30 days)
    tweets = fetcher.fetch_all_user_activity(username)
    print(f"Found {len(tweets)} tweets")
    
    if not tweets:
        print("No tweets found. Please check the username and try again.")
        db.close()
        return
    
    # Store tweets in database
    for tweet in tweets:
        db.store_tweet(tweet)
    
    # Generate identity summary
    print("\nGenerating identity summary...")
    previous_summary = db.get_latest_identity_summary()
    summary, analysis = analyzer.generate_identity_summary(
        tweets,
        previous_summary["summary_text"] if previous_summary else None
    )
    
    if summary:
        print("\nIdentity Summary:")
        print(summary)
        print("\nPersonality Traits:")
        for trait, score in analysis["personality_traits"].items():
            print(f"- {trait}: {score:.2f}")
        print("\nInterests:")
        for interest, score in analysis["interests"].items():
            print(f"- {interest}: {score:.2f}")
        print("\nCommon Topics:")
        for topic in analysis["common_topics"]:
            print(f"- {topic}")
            
        # Store the summary
        db.store_identity_summary(
            summary,
            analysis["personality_traits"],
            analysis["interests"],
            analysis["common_topics"],
            analysis["confidence_scores"]
        )
    
    # Generate weekly summary for the last week
    print("\nGenerating weekly summary...")
    week_start = datetime.now() - timedelta(days=7)
    week_tweets = db.get_tweets_for_timeframe(week_start, datetime.now())
    
    if week_tweets:
        summary, topics, metrics = analyzer.generate_weekly_summary(week_tweets)
        
        if summary:
            print("\nWeekly Summary:")
            print(summary)
            print("\nTopics Discussed:")
            for topic in topics:
                print(f"- {topic}")
            print("\nEngagement Metrics:")
            print(f"Average Likes: {metrics['avg_likes']}")
            print(f"Average Retweets: {metrics['avg_retweets']}")
            print("\nTop Tweet Topics:")
            for topic in metrics["top_tweet_topics"]:
                print(f"- {topic}")
                
            # Store the weekly summary
            db.store_weekly_summary(
                week_start,
                datetime.now(),
                summary,
                topics,
                metrics
            )
    else:
        print("\nNo tweets found in the last week.")
    
    # Clean up
    db.optimize_database()
    db.close()

if __name__ == "__main__":
    main() 