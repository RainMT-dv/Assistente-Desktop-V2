"""Mood Engine - Sistema de humor persistente do Assistente."""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional


class MoodEngine:
    """Sistema de humor persistente do Assistente."""
    
    # Mood vai de -10 (irritada) a +10 (animada), 0 = neutro
    MOOD_LABELS = {
        (-10, -7): "Irritada",
        (-6, -3): "Chateada", 
        (-2, 2): "Neutra",
        (3, 6): "Animada",
        (7, 10): "Eufórica"
    }
    
    def __init__(self, filepath: str = "data/mood.json"):
        """Inicializa o engine de mood."""
        self.filepath = filepath
        self.mood = 0  # -10 a +10
        self.mood_history = []  # Track de mudanças
        self.last_decay = datetime.now()
        self._load_mood()
    
    def _load_mood(self) -> None:
        """Carrega mood do arquivo se existir."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.mood = data.get('mood', 0)
                    self.mood_history = data.get('history', [])
                    last_decay_str = data.get('last_decay')
                    if last_decay_str:
                        self.last_decay = datetime.fromisoformat(last_decay_str)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[ERRO] Falha ao carregar mood: {e}")
    
    def save(self) -> None:
        """Salva mood no arquivo."""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        
        data = {
            'mood': self.mood,
            'label': self.get_mood_label(),
            'history': self.mood_history[-50:],  # Mantém últimas 50 mudanças
            'last_decay': self.last_decay.isoformat(),
            'saved_at': datetime.now().isoformat()
        }
        
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def update_mood(self, user_emotion: str, user_text: str) -> None:
        """Atualiza mood baseado na interação."""
        old_mood = self.mood
        user_lower = user_text.lower()
        
        # Palavras positivas
        positive_words = [
            "obrigado", "obrigada", "valeu", "legal", "top", "demais", 
            "bom", "boa", "incrível", "maravilhoso", "amei", "adorei",
            "feliz", "alegre", "contente", "animado", "animada",
            "haha", "kkk", "rsrs", "engraçado", "engraçada", "divertido"
        ]
        
        # Palavras negativas
        negative_words = [
            "ruim", "péssimo", "péssima", "horrível", "terrível", "ódio",
            "odeio", "raiva", "irritado", "irritada", "chateado", "chateada",
            "estúpido", "estúpida", "idiota", "burro", "burra", "merda",
            "droga", "caralho", "cacete", "inferno", "vai se foder",
            "não gosto", "odeio", "desgraça", "vexame"
        ]
        
        # Elogios direcionados à IA
        praise_words = [
            "você é boa", "você é foda", "você é incrível", "você é top",
            "gosto de você", "adoro você", "você é engraçada", "você manda bem",
            "que resposta boa", "muito bom", "muito boa", "perfeito", "perfeita"
        ]
        
        # Xingamentos direcionados à IA
        insult_words = [
            "você é ruim", "você é burra", "você é estúpida", "não gosto de você",
            "odeio você", "você é inútil", "você não presta", "sua idiota",
            "sua burra", "sua estúpida", "calada", "cala a boca", "shut up"
        ]
        
        change = 0
        reason = ""
        
        # Detectar elogios (maior impacto positivo)
        for word in praise_words:
            if word in user_lower:
                change += 2
                reason = "elogio"
                break
        
        # Detectar insultos (maior impacto negativo)
        if change == 0:  # Só checa insultos se não foi elogio
            for word in insult_words:
                if word in user_lower:
                    change -= 2
                    reason = "insulto"
                    break
        
        # Detectar palavras positivas/negativas gerais
        if change == 0:
            positive_count = sum(1 for w in positive_words if w in user_lower)
            negative_count = sum(1 for w in negative_words if w in user_lower)
            
            if positive_count > negative_count:
                change = 1
                reason = "positividade"
            elif negative_count > positive_count:
                change = -1
                reason = "negatividade"
        
        # Emoção do usuário afeta mood (simplificado)
        if user_emotion == "Feliz":
            change += 1  # Contágio de alegria
            reason = reason or "contágio positivo"
        
        # Aplicar mudança
        self.mood = max(-10, min(10, self.mood + change))
        
        # Log mudança
        if change != 0:
            self.mood_history.append({
                'timestamp': datetime.now().isoformat(),
                'change': change,
                'from': old_mood,
                'to': self.mood,
                'reason': reason,
                'user_text': user_text[:50]
            })
            print(f"[MOOD] {old_mood} → {self.mood} ({reason}: {change:+.0f})")
    
    def get_mood_label(self) -> str:
        """Retorna label do mood atual."""
        for (min_m, max_m), label in self.MOOD_LABELS.items():
            if min_m <= self.mood <= max_m:
                return label
        return "Neutra"
    
    def get_mood_modifier(self) -> Dict:
        """Retorna modificadores de personalidade baseado no mood."""
        label = self.get_mood_label()
        
        modifiers = {
            "Irritada": {
                "sarcasm_boost": 1.5,
                "response_length": "curta",
                "aggression": 1.3,
                "patience": 0.3,
                "tone": "agressivo",
                "empathy": 0.2
            },
            "Chateada": {
                "sarcasm_boost": 1.2,
                "response_length": "média_curta",
                "aggression": 1.1,
                "patience": 0.5,
                "tone": "reservado",
                "empathy": 0.5
            },
            "Neutra": {
                "sarcasm_boost": 1.0,
                "response_length": "normal",
                "aggression": 1.0,
                "patience": 1.0,
                "tone": "normal",
                "empathy": 1.0
            },
            "Animada": {
                "sarcasm_boost": 1.1,
                "response_length": "longa",
                "aggression": 0.9,
                "patience": 1.2,
                "tone": "brincalhão",
                "empathy": 1.1
            },
            "Eufórica": {
                "sarcasm_boost": 1.3,
                "response_length": "longa",
                "aggression": 0.7,
                "patience": 1.5,
                "tone": "hiperativo",
                "empathy": 1.2
            }
        }
        
        return modifiers.get(label, modifiers["Neutra"])
    
    def get_mood_prompt(self) -> str:
        """Retorna texto para injetar no system prompt."""
        label = self.get_mood_label()
        modifiers = self.get_mood_modifier()
        
        prompts = {
            "Irritada": "Você está IRRITADA hoje. Respostas curtas, sarcásticas, sem paciência. Se o usuário der mole, zoe sem dó.",
            "Chateada": "Você está CHATEADA. Menos energia, mais reservada, mas ainda debochada quando provocada.",
            "Neutra": "",  # Não adiciona nada
            "Animada": "Você está ANIMADA! Mais energia, mais zoeira, respostas mais longas e divertidas.",
            "Eufórica": "Você está EUFÓRICA! Muita energia, muita zoeira, hyperativa, respostas longas e cheias de piadas."
        }
        
        return prompts.get(label, "")
    
    def decay_mood(self) -> bool:
        """Mood tende lentamente a 0 ao longo do tempo. Chamado periodicamente."""
        now = datetime.now()
        time_since_last = now - self.last_decay
        
        # Decay a cada 5 minutos
        if time_since_last >= timedelta(minutes=5):
            old_mood = self.mood
            
            if self.mood > 0:
                self.mood = max(0, self.mood - 1)  # Decai 1 ponto positivo
            elif self.mood < 0:
                self.mood = min(0, self.mood + 1)  # Decai 1 ponto negativo
            
            self.last_decay = now
            
            if self.mood != old_mood:
                print(f"[MOOD] Decay: {old_mood} → {self.mood}")
                return True
        
        return False
    
    def get_mood_display(self) -> str:
        """Retorna string para display no dashboard."""
        label = self.get_mood_label()
        mood_emoji = {
            "Irritada": "😠",
            "Chateada": "😒",
            "Neutra": "😐",
            "Animada": "😊",
            "Eufórica": "🤩"
        }.get(label, "😐")
        
        bar_length = 20
        position = int((self.mood + 10) / 20 * bar_length)
        position = max(0, min(bar_length, position))
        
        bar = ["-"] * bar_length
        bar[position] = "●"
        bar_str = f"[{''.join(bar)}]"
        
        return f"{mood_emoji} {label} ({self.mood:+.0f}) {bar_str}"


if __name__ == "__main__":
    # Testes
    mood = MoodEngine("test_mood.json")
    
    print("Teste de MoodEngine:")
    print(f"Mood inicial: {mood.get_mood_display()}")
    
    # Simula interações
    mood.update_mood("Feliz", "Você é muito boa! Adoro falar com você")
    print(f"Após elogio: {mood.get_mood_display()}")
    
    mood.update_mood("Neutra", "Ok, entendi")
    print(f"Após resposta neutra: {mood.get_mood_display()}")
    
    print(f"\nModifier: {mood.get_mood_modifier()}")
    print(f"Prompt: {mood.get_mood_prompt()}")
    
    mood.save()
    print(f"\nSalvo em: {mood.filepath}")
