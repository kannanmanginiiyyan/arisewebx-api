import re
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime

class SearchEngine:
    """Semantic search engine for the knowledge base"""
    
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.search_history = []
    
    def keyword_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Simple keyword-based search using inverted index"""
        query_words = re.findall(r'\b\w+\b', query.lower())
        
        # Score each chunk
        scores = {}
        for word in query_words:
            if word in self.kb.index:
                for chunk_id, score in self.kb.index[word].items():
                    scores[chunk_id] = scores.get(chunk_id, 0) + score
        
        # Get top results
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Return actual chunks
        results = []
        for chunk_id, score in sorted_results:
            chunk = next((c for c in self.kb.chunks if c['id'] == chunk_id), None)
            if chunk:
                results.append({
                    "chunk": chunk,
                    "score": float(score),  # Convert to float for JSON serialization
                    "search_type": "keyword"
                })
        
        return results
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Simple semantic search using word overlap and similarity"""
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        
        results = []
        for chunk in self.kb.chunks:
            content_words = set(re.findall(r'\b\w+\b', chunk['content'].lower()))
            
            # Calculate Jaccard similarity
            intersection = len(query_words.intersection(content_words))
            union = len(query_words.union(content_words))
            
            if union > 0:
                jaccard = intersection / union
            else:
                jaccard = 0
            
            # Boost score for matching keywords
            keyword_boost = 0
            for keyword in chunk.get('keywords', []):
                if keyword.lower() in query.lower():
                    keyword_boost += 0.3
            
            final_score = jaccard + keyword_boost
            
            if final_score > 0:
                results.append({
                    "chunk": chunk,
                    "score": float(final_score),  # Convert to float
                    "search_type": "semantic"
                })
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Record search history
        self.search_history.append({
            "query": query,
            "results_count": len(results[:top_k]),
            "timestamp": datetime.now().isoformat()
        })
        
        return results[:top_k]
    
    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Combine keyword and semantic search for best results"""
        keyword_results = self.keyword_search(query, top_k)
        semantic_results = self.semantic_search(query, top_k)
        
        # Combine and deduplicate
        combined = {}
        
        for result in keyword_results:
            chunk_id = result['chunk']['id']
            combined[chunk_id] = {
                "chunk": result['chunk'],
                "keyword_score": result['score'],
                "semantic_score": 0.0,
                "search_type": "hybrid"
            }
        
        for result in semantic_results:
            chunk_id = result['chunk']['id']
            if chunk_id in combined:
                combined[chunk_id]['semantic_score'] = result['score']
            else:
                combined[chunk_id] = {
                    "chunk": result['chunk'],
                    "keyword_score": 0.0,
                    "semantic_score": result['score'],
                    "search_type": "hybrid"
                }
        
        # Calculate final score (70% semantic, 30% keyword)
        for chunk_id in combined:
            combined[chunk_id]['final_score'] = float(
                combined[chunk_id]['semantic_score'] * 0.7 +
                combined[chunk_id]['keyword_score'] * 0.3
            )
        
        # Sort and return
        results = sorted(combined.values(), key=lambda x: x['final_score'], reverse=True)[:top_k]
        
        return results
    
    def answer_question(self, query: str) -> Dict:
        """Generate answer from search results"""
        results = self.hybrid_search(query, top_k=3)
        
        if not results:
            return {
                "answer": "I couldn't find information about that. Please contact AriseWebX directly at arisewebx@gmail.com",
                "sources": [],
                "confidence": 0.0
            }
        
        # Extract answer from best result
        best_result = results[0]
        content = best_result['chunk']['content']
        
        # Format answer based on query type
        query_lower = query.lower()
        
        if 'contact' in query_lower or 'email' in query_lower:
            emails = []
            for chunk in self.kb.chunks:
                if chunk['metadata'].get('type') == 'contact':
                    found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', chunk['content'])
                    emails.extend(found_emails)
            if emails:
                # Remove duplicates and your@example.com
                emails = [e for e in set(emails) if e != 'your@example.com']
                answer = f"You can contact AriseWebX at: {', '.join(emails)}"
            else:
                answer = content
                
        elif 'social' in query_lower or 'instagram' in query_lower or 'linkedin' in query_lower or 'twitter' in query_lower:
            social_links = []
            for chunk in self.kb.chunks:
                if chunk['metadata'].get('type') == 'social':
                    social_links.append(chunk['content'])
            # Remove duplicates
            if social_links:
                answer = social_links[0]  # Take first one since they're duplicates
            else:
                answer = content
            
        elif 'service' in query_lower or 'offer' in query_lower:
            services = []
            for chunk in self.kb.chunks:
                if chunk['metadata'].get('type') == 'services':
                    services.append(chunk['content'])
            answer = "\n".join(services) if services else content
            
        else:
            answer = content
        
        return {
            "answer": answer,
            "sources": [r['chunk']['metadata'] for r in results],
            "confidence": float(best_result.get('final_score', 0.5)),
            "search_results": results
        }
    
    def get_search_stats(self) -> Dict:
        """Get search statistics"""
        return {
            "total_searches": len(self.search_history),
            "recent_queries": self.search_history[-5:],
            "total_chunks": len(self.kb.chunks),
            "index_size": len(self.kb.index)
        }