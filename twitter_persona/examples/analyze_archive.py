import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.database.database import TwitterDatabase
from src.fetcher.archive_fetcher import TwitterArchiveFetcher
from src.analyzer.tweet_analyzer import TweetAnalyzer

def main():
    # Load environment variables (still need ANTHROPIC_API_KEY for analysis)
    load_dotenv()
    
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    # Initialize components
    db = TwitterDatabase()
    fetcher = TwitterArchiveFetcher()
    analyzer = TweetAnalyzer()
    
    # Get archive path from user
    print("\nPlease provide the path to your Twitter archive.")
    print("This can be either the unzipped directory or the tweets.js file.")
    archive_path = input("Archive path: ")
    
    print(f"\nLoading tweets from archive: {archive_path}")
    
    # Check if it's a directory or file
    if os.path.isdir(archive_path):
        tweets = fetcher.process_archive_directory(archive_path)
    else:
        tweets = fetcher.load_archive(archive_path)
    
    print(f"Found {len(tweets)} tweets")
    
    if not tweets:
        print("No tweets found. Please check the archive path and try again.")
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
    
    # Generate weekly summary for the most recent week in the archive
    print("\nGenerating weekly summary...")
    latest_date = max(t["created_at"] for t in tweets)
    week_start = latest_date - timedelta(days=7)
    week_tweets = [t for t in tweets if week_start <= t["created_at"] <= latest_date]
    
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
                latest_date,
                summary,
                topics,
                metrics
            )
    else:
        print("\nNo tweets found in the most recent week.")
    
    # Clean up
    db.optimize_database()
    db.close()

if __name__ == "__main__":
    main() 