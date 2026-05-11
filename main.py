import sys
from engine import AdvisoryEngine

def print_advisory(item):
    score = item.get('similarity_score')
    score_str = f" [Match: {score:.1%}]" if score else ""
    
    print("-" * 40)
    print(f"CROP      : {item['crop']}{score_str}")
    print(f"SYMPTOM   : {item['symptom']}")
    print(f"CAUSE     : {item['cause']}")
    print(f"SOLUTION  : {item['solution']}")
    print(f"PREVENTION: {item['prevention']}")
    print("-" * 40)

def main():
    print("========================================")
    print("   OFFLINE FARMER ADVISORY SYSTEM      ")
    print("        (Semantic Search Enabled)      ")
    print("========================================")
    
    try:
        engine = AdvisoryEngine()
    except Exception as e:
        print(f"Error initializing system: {e}")
        return

    print("\nReady! Type your query (e.g., 'hot weather ragi' or 'rice yellowing')")
    print("Type 'exit' to quit.")
    print("")

    while True:
        try:
            query = input("Farmer Query > ").strip()
            if query.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            
            if not query:
                continue

            results = engine.search(query)
            
            if results:
                print(f"\nFound {len(results)} relevant advisory/advisories:\n")
                for item in results:
                    print_advisory(item)
            else:
                print("\nNo matching advisories found. Try different keywords.\n")
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
