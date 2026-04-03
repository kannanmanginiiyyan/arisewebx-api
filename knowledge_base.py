import json
import pickle
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime
import re
from collections import defaultdict

class KnowledgeBase:
    """Manages the scraped data as structured knowledge"""
    
    def __init__(self, data_file: str = "arisewebx_scraped_data.json"):
        self.data_file = data_file
        self.raw_data = None
        self.knowledge_graph = {}
        self.embeddings = {}
        self.chunks = []
        self.index = {}
        
    def load_data(self) -> bool:
        """Load scraped data from JSON file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.raw_data = json.load(f)
            print(f"✅ Loaded data from {self.data_file}")
            return True
        except FileNotFoundError:
            print(f"❌ File {self.data_file} not found. Run scraper first.")
            return False
    
    def build_knowledge_graph(self):
        """Convert raw data into structured knowledge graph"""
        print("Building knowledge graph...")
        
        for url, data in self.raw_data.items():
            kg = {
                "entities": [],
                "relationships": [],
                "attributes": {}
            }
            
            # Extract entities
            # Business entity
            if data.get('business_info'):
                kg["entities"].append({
                    "type": "Business",
                    "name": data['business_info'].get('name', 'AriseWebX'),
                    "properties": data['business_info']
                })
            
            # Social media entities
            for platform, link in data.get('social_media_links', {}).items():
                kg["entities"].append({
                    "type": "SocialMedia",
                    "platform": platform,
                    "url": link
                })
                kg["relationships"].append({
                    "from": "Business",
                    "to": platform,
                    "type": "has_social_media"
                })
            
            # Contact entities
            for email in data.get('emails', []):
                kg["entities"].append({
                    "type": "Contact",
                    "method": "email",
                    "value": email
                })
                kg["relationships"].append({
                    "from": "Business",
                    "to": email,
                    "type": "contact_via"
                })
            
            # Service entities
            for service in data.get('services', []):
                kg["entities"].append({
                    "type": "Service",
                    "name": service
                })
                kg["relationships"].append({
                    "from": "Business",
                    "to": service,
                    "type": "offers"
                })
            
            # Store knowledge
            self.knowledge_graph[url] = kg
        
        print(f"✅ Knowledge graph built with {sum(len(kg['entities']) for kg in self.knowledge_graph.values())} entities")
    
    def create_text_chunks(self):
        """Create searchable text chunks from all data"""
        print("Creating text chunks...")
        
        chunks = []
        
        for url, data in self.raw_data.items():
            # Business info chunk
            if data.get('business_info'):
                biz = data['business_info']
                chunk = {
                    "id": f"{url}_business",
                    "content": f"{biz.get('name', 'AriseWebX')} is a web design agency. {biz.get('description', '')}",
                    "metadata": {"type": "business_info", "url": url},
                    "keywords": ["business", "company", "agency"]
                }
                chunks.append(chunk)
            
            # Services chunk
            if data.get('services'):
                services_text = "We offer: " + ", ".join(data['services'])
                chunk = {
                    "id": f"{url}_services",
                    "content": services_text,
                    "metadata": {"type": "services", "url": url},
                    "keywords": ["service", "offer", "provide"] + data['services']
                }
                chunks.append(chunk)
            
            # Social media chunk
            if data.get('social_media_links'):
                social_text = "Social media presence: "
                for platform, link in data['social_media_links'].items():
                    social_text += f"{platform}: {link}. "
                chunk = {
                    "id": f"{url}_social",
                    "content": social_text,
                    "metadata": {"type": "social", "url": url},
                    "keywords": ["social", "instagram", "linkedin", "twitter", "facebook"]
                }
                chunks.append(chunk)
            
            # Contact chunk
            if data.get('emails') or data.get('phones'):
                contact_text = "Contact information: "
                if data.get('emails'):
                    contact_text += f"Emails: {', '.join(data['emails'])}. "
                if data.get('phones'):
                    contact_text += f"Phones: {', '.join(data['phones'])}. "
                chunk = {
                    "id": f"{url}_contact",
                    "content": contact_text,
                    "metadata": {"type": "contact", "url": url},
                    "keywords": ["contact", "email", "phone", "reach"]
                }
                chunks.append(chunk)
            
            # Meta tags chunk
            if data.get('meta_tags'):
                meta_text = "SEO and meta information: "
                important_tags = ['description', 'keywords', 'og:title', 'og:description']
                for tag in important_tags:
                    if tag in data['meta_tags']:
                        meta_text += f"{tag}: {data['meta_tags'][tag]}. "
                chunk = {
                    "id": f"{url}_meta",
                    "content": meta_text,
                    "metadata": {"type": "meta", "url": url},
                    "keywords": ["seo", "meta", "description", "title"]
                }
                chunks.append(chunk)
            
            # Hidden data chunk
            if data.get('hidden_data'):
                hidden = data['hidden_data']
                if hidden.get('hidden_elements'):
                    hidden_text = "Hidden content: "
                    for elem in hidden['hidden_elements'][:3]:
                        if elem.get('text'):
                            hidden_text += elem['text'][:200] + ". "
                    chunk = {
                        "id": f"{url}_hidden",
                        "content": hidden_text,
                        "metadata": {"type": "hidden", "url": url},
                        "keywords": ["hidden", "data", "attribute"]
                    }
                    chunks.append(chunk)
            
            # Headings chunk
            if data.get('headings'):
                headings_text = "Page structure: "
                for level in ['h1', 'h2', 'h3']:
                    if data['headings'].get(level):
                        headings_text += f"{level.upper()}: {', '.join(data['headings'][level][:3])}. "
                chunk = {
                    "id": f"{url}_headings",
                    "content": headings_text,
                    "metadata": {"type": "structure", "url": url},
                    "keywords": ["heading", "structure", "content"]
                }
                chunks.append(chunk)
        
        self.chunks = chunks
        print(f"✅ Created {len(chunks)} searchable chunks")
    
    def build_inverted_index(self):
        """Build simple inverted index for keyword search"""
        print("Building inverted index...")
        
        inverted_index = defaultdict(lambda: defaultdict(float))
        
        for chunk in self.chunks:
            chunk_id = chunk['id']
            content = chunk['content'].lower()
            keywords = chunk.get('keywords', [])
            
            # Add keywords with higher weight
            for keyword in keywords:
                inverted_index[keyword][chunk_id] = 2.0
            
            # Add words from content
            words = re.findall(r'\b\w+\b', content)
            word_freq = defaultdict(int)
            for word in words:
                if len(word) > 2:  # Ignore short words
                    word_freq[word] += 1
            
            total_words = len(words)
            for word, freq in word_freq.items():
                tf = freq / total_words
                inverted_index[word][chunk_id] = max(inverted_index[word].get(chunk_id, 0), tf)
        
        self.index = dict(inverted_index)
        print(f"✅ Built index with {len(self.index)} unique terms")
    
    def save_knowledge(self, filepath: str = "knowledge_base.pkl"):
        """Save knowledge base to disk"""
        knowledge = {
            "knowledge_graph": self.knowledge_graph,
            "chunks": self.chunks,
            "index": self.index,
            "raw_data": self.raw_data
        }
        with open(filepath, 'wb') as f:
            pickle.dump(knowledge, f)
        print(f"✅ Knowledge base saved to {filepath}")
    
    def load_knowledge(self, filepath: str = "knowledge_base.pkl"):
        """Load knowledge base from disk"""
        try:
            with open(filepath, 'rb') as f:
                knowledge = pickle.load(f)
            self.knowledge_graph = knowledge["knowledge_graph"]
            self.chunks = knowledge["chunks"]
            self.index = knowledge["index"]
            self.raw_data = knowledge["raw_data"]
            print(f"✅ Knowledge base loaded from {filepath}")
            return True
        except FileNotFoundError:
            print(f"❌ Knowledge file {filepath} not found")
            return False

