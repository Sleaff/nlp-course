from email.mime import text
from afinn import Afinn

def main():
    afinn = Afinn()

    def sentiment(text: str) -> str:
        score = afinn.score(text)
        return 'positive' if score > 0 else 'negative' if score < 0 else 'neutral'
    

    print(sentiment("I love this movie!"))
    print(sentiment("This movie is terrible."))
    print(sentiment("This movie is okay."))


if __name__ == "__main__":
    main()