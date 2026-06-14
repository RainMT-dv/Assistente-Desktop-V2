"""Web Search Skill - Busca na web via DuckDuckGo."""

import aiohttp
import asyncio
from typing import List, Dict, Optional
from urllib.parse import quote


class WebSearchSkill:
    """Skill para busca na web usando DuckDuckGo."""
    
    def __init__(self):
        """Inicializa o skill de busca."""
        self.base_url = "https://html.duckduckgo.com/html/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
        }
    
    async def search(self, query: str, max_results: int = 3) -> List[Dict]:
        """
        Busca na web e retorna resultados.
        
        Args:
            query: Termo de busca
            max_results: Número máximo de resultados
            
        Returns:
            Lista de resultados com título, URL e snippet
        """
        try:
            encoded_query = quote(query)
            url = f"{self.base_url}?q={encoded_query}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=10) as response:
                    if response.status != 200:
                        return []
                    
                    html = await response.text()
                    return self._parse_results(html, max_results)
                    
        except Exception as e:
            print(f"[WEB SEARCH] Erro: {e}")
            return []
    
    def _parse_results(self, html: str, max_results: int) -> List[Dict]:
        """Parseia HTML dos resultados."""
        from bs4 import BeautifulSoup
        
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # DuckDuckGo HTML structure
        for result in soup.find_all('div', class_='result', limit=max_results):
            try:
                title_tag = result.find('a', class_='result__a')
                snippet_tag = result.find('a', class_='result__snippet')
                
                if title_tag and snippet_tag:
                    title = title_tag.get_text(strip=True)
                    url = title_tag.get('href', '')
                    snippet = snippet_tag.get_text(strip=True)
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet[:200]  # Limita snippet
                    })
            except:
                continue
        
        return results
    
    def format_for_context(self, results: List[Dict]) -> str:
        """Formata resultados para injetar no contexto."""
        if not results:
            return ""
        
        lines = ["[INFORMAÇÃO DA WEB - use naturalmente na resposta:]"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r['title']}: {r['snippet']}")
        
        return "\n".join(lines)
    
    def should_search(self, user_text: str) -> tuple[bool, str]:
        """
        Detecta se deve fazer busca baseado no input do usuário.
        
        Returns:
            (deve_buscar, query_otimizado)
        """
        text_lower = user_text.lower()
        
        # Palavras-chave que indicam necessidade de busca
        search_triggers = [
            "quem é", "o que é", "quando foi", "onde fica", "como funciona",
            "notícias sobre", "preço de", "receita de", "significado de",
            "wikipedia", "google", "pesquisa", "busca", "informação sobre"
        ]
        
        for trigger in search_triggers:
            if trigger in text_lower:
                # Remove o trigger da query
                query = user_text.lower().replace(trigger, "").strip()
                query = query.strip("?").strip()
                if len(query) > 3:
                    return True, query
        
        return False, ""


# Instância global
_web_search = None

async def get_web_search_skill() -> WebSearchSkill:
    """Retorna instância singleton do WebSearchSkill."""
    global _web_search
    if _web_search is None:
        _web_search = WebSearchSkill()
    return _web_search


if __name__ == "__main__":
    # Teste
    async def test():
        skill = WebSearchSkill()
        results = await skill.search("python programming", max_results=2)
        print(f"Encontrados {len(results)} resultados:")
        for r in results:
            print(f"  - {r['title']}: {r['snippet'][:60]}...")
    
    asyncio.run(test())
