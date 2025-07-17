"""it's under development, don't use it yet. it's not even tested."""


from ddgs import DDGS

def search_links(query: str, max_results: int = 5):
    with DDGS() as ddg:
        return list(ddg.text(query, max_results=max_results))

import requests
from bs4 import BeautifulSoup

def fetch_full_text(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        paragraphs = soup.find_all("p")
        return "\n".join(p.get_text().strip() for p in paragraphs if len(p.get_text()) > 40)
    except Exception as e:
        return f"[ERROR] {e}"

import ollama

def summarize_text(text: str, model: str = "llama3.1") -> str:
    prompt = f"""Summarize the following content in clear, simple terms:\n\n{text}"""
    result = ollama.chat(model=model, messages=[
        {"role": "user", "content": prompt}
    ]) 
    return result["message"]["content"]

def intelligent_search(query: str, max_results: int = 3):
    results = search_links(query, max_results)
    summaries = []

    for r in results:
        print(f"\n🔍 {r['title']}")
        text = fetch_full_text(r["href"])
        summary = summarize_text(text[:3000])  # قلل لو النص كبير
        summaries.append({"url": r["href"], "summary": summary})
    
    return summaries


def main():
    query = input("Enter your search query: ")
    results = intelligent_search(query)
    for result in results:
        print(f"URL: {result['url']}")
        print(f"Summary: {result['summary']}\n")
        

if __name__ == "__main__":
    main()