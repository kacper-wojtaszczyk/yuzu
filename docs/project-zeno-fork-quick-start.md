# Project Zeno Fork: Quick Start Guide

## 🎯 What We're Building

**Fork of [wri/project-zeno](https://github.com/wri/project-zeno)** with experimental narrative tools added to their LangGraph agent.

### Planned Narrative Tools

| Tool | Description | Priority | Complexity | Dependencies |
|------|-------------|----------|------------|--------------|
| **🖊️ Haiku Generator** | 5-7-5 syllable poetic form | ⭐⭐⭐ High | Low | LLM + syllable counter |
| **🎵 Soundscape Generator** | Audio representations | ⭐⭐ Medium | Medium | Audio APIs + storage |
| **📖 Speculative Fiction** | "What if" stories | ⭐⭐ Medium | Medium | LLM + prompting |
| **🌍 Parallel Earths** | Alternate timeline viz | ⭐ Low | High | Carbon models + viz |
| **🎨 Image Generation** | Visual storytelling | ⭐ Stretch | Medium | Image APIs + storage |

### Recommended Starting Order

1. **Week 1-2**: Fork, setup, understand codebase
2. **Week 3-4**: **Haiku Generator** (simplest, proves concept)
3. **Week 5-6**: **Soundscape Generator** (audio experiment)
4. **Week 7+**: Other tools as time/interest permits

---

## 📁 File Structure (Our Additions)

```
project-zeno-narrative-experiments/
├── src/
│   ├── narrative_tools/          # NEW: Our narrative generators
│   │   ├── __init__.py
│   │   ├── haiku.py              # Haiku generation logic
│   │   ├── soundscape.py         # Audio generation logic
│   │   ├── fiction.py            # Speculative fiction engine
│   │   └── parallel_earths.py    # Counterfactual simulator
│   └── agent/
│       └── tools/
│           ├── narrative_haiku.py        # NEW: Agent tool wrapper
│           └── narrative_soundscape.py   # NEW: Agent tool wrapper
├── tests/
│   └── narrative_tools/          # NEW: Tests for our tools
│       ├── test_haiku.py
│       └── test_soundscape.py
└── docs/
    └── narrative_tools/          # NEW: Tool documentation
        ├── haiku.md
        └── soundscape.md
```

---

## 🛠️ Example: Haiku Generator Implementation

### 1. Core Generator (`src/narrative_tools/haiku.py`)

```python
"""
Haiku generator for forest change narratives.
Transforms quantitative forest loss data into 5-7-5 syllable poetic form.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field
import pyphen  # For syllable counting

class HaikuInput(BaseModel):
    forest_loss_ha: float = Field(description="Forest loss in hectares")
    region_name: str = Field(description="Name of affected region")
    time_period: str = Field(description="Time period (e.g., 'October 2024')")

class HaikuOutput(BaseModel):
    haiku: str = Field(description="Generated haiku (3 lines)")
    syllable_count: tuple[int, int, int] = Field(description="Syllables per line")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class HaikuGenerator:
    """Generate haiku from forest loss data."""
    
    def __init__(self, llm_client=None):
        self.llm = llm_client or self._default_llm()
        self.syllable_counter = pyphen.Pyphen(lang='en')
    
    def generate(self, input_data: HaikuInput) -> HaikuOutput:
        """Generate haiku with strict 5-7-5 syllable constraint."""
        
        prompt = f"""
        Write a haiku (5-7-5 syllables) about this forest loss:
        - Location: {input_data.region_name}
        - Amount: {input_data.forest_loss_ha:.0f} hectares
        - Time: {input_data.time_period}
        
        Requirements:
        - Line 1: 5 syllables
        - Line 2: 7 syllables  
        - Line 3: 5 syllables
        - Focus on concrete imagery and emotion
        - Reference the data naturally
        
        Return only the haiku, one line per line.
        """
        
        max_retries = 3
        for attempt in range(max_retries):
            haiku = self.llm.generate(prompt)
            lines = haiku.strip().split('\n')
            
            if len(lines) != 3:
                continue
                
            syllables = tuple(self._count_syllables(line) for line in lines)
            
            if syllables == (5, 7, 5):
                return HaikuOutput(
                    haiku=haiku,
                    syllable_count=syllables,
                    metadata={"attempts": attempt + 1}
                )
        
        raise ValueError(f"Failed to generate valid haiku after {max_retries} attempts")
    
    def _count_syllables(self, text: str) -> int:
        """Count syllables in text."""
        words = text.split()
        return sum(len(self.syllable_counter.positions(word)) + 1 for word in words)
    
    def _default_llm(self):
        """Get default LLM (reuse project-zeno's setup)."""
        # Import and use their LLM client
        from src.agent.llm import get_llm_client
        return get_llm_client()
```

### 2. Agent Tool Wrapper (`src/agent/tools/narrative_haiku.py`)

```python
"""Agent tool for haiku generation."""

from langchain.tools import tool
from src.narrative_tools.haiku import HaikuGenerator, HaikuInput

@tool
def generate_forest_haiku(
    forest_loss_ha: float,
    region_name: str,
    time_period: str
) -> str:
    """
    Generate a haiku about forest loss.
    
    Transforms forest change data into 5-7-5 syllable poetic format.
    Use when user requests poetic, minimalist, or emotional interpretations.
    
    Args:
        forest_loss_ha: Amount of forest lost in hectares
        region_name: Geographic location
        time_period: Temporal scope (e.g., "October 2024")
    
    Returns:
        Three-line haiku with 5-7-5 syllable pattern
    """
    generator = HaikuGenerator()
    input_data = HaikuInput(
        forest_loss_ha=forest_loss_ha,
        region_name=region_name,
        time_period=time_period
    )
    result = generator.generate(input_data)
    return result.haiku
```

### 3. Register Tool with Agent (`src/agent/graph.py`)

```python
# Add to existing imports
from src.agent.tools.narrative_haiku import generate_forest_haiku

# Add to tools list (find where other tools are registered)
tools = [
    # ... existing tools ...
    generate_forest_haiku,  # NEW: Add our haiku tool
]
```

### 4. Test (`tests/narrative_tools/test_haiku.py`)

```python
import pytest
from src.narrative_tools.haiku import HaikuGenerator, HaikuInput

def test_haiku_syllable_count():
    """Generated haiku must have 5-7-5 syllable pattern."""
    generator = HaikuGenerator()
    input_data = HaikuInput(
        forest_loss_ha=450.0,
        region_name="Paraná",
        time_period="October 2024"
    )
    
    result = generator.generate(input_data)
    
    assert result.syllable_count == (5, 7, 5)
    assert len(result.haiku.split('\n')) == 3

def test_haiku_references_data():
    """Haiku should reference input data."""
    generator = HaikuGenerator()
    input_data = HaikuInput(
        forest_loss_ha=450.0,
        region_name="Paraná",
        time_period="October"
    )
    
    result = generator.generate(input_data)
    haiku_lower = result.haiku.lower()
    
    # Should mention location or time
    assert any(term in haiku_lower for term in ["paraná", "october", "autumn", "fall"])
```

---

## 🚀 Getting Started

### 1. Fork & Setup

```bash
# Fork on GitHub: wri/project-zeno → your-username/project-zeno-narrative-experiments

# Clone your fork
git clone https://github.com/your-username/project-zeno-narrative-experiments.git
cd project-zeno-narrative-experiments

# Add upstream remote
git remote add upstream https://github.com/wri/project-zeno.git

# Install dependencies
uv sync

# Copy environment config
cp .env.example .env
# Edit .env with your API keys

# Start database and services
make up

# Verify setup
uv run pytest
```

### 2. Study the Codebase (Week 1)

**Key files to understand:**
- `src/agent/graph.py` — How agent is structured
- `src/agent/tools/*.py` — Existing tool patterns
- `src/api/routes.py` — API endpoint patterns
- `tests/agent/*.py` — Testing patterns

**Run existing examples:**
```bash
# Start API
make api

# In another terminal, test chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the forest loss in the Amazon this year?"}'
```

### 3. Build First Tool (Weeks 2-3)

Pick **Haiku Generator** as starting point:

```bash
# Create feature branch
git checkout -b feature/haiku-generator

# Create files (see structure above)
touch src/narrative_tools/haiku.py
touch src/agent/tools/narrative_haiku.py
touch tests/narrative_tools/test_haiku.py

# Implement (see examples above)

# Test
uv run pytest tests/narrative_tools/test_haiku.py -v

# Document
touch docs/narrative_tools/haiku.md

# Commit (human does this, not AI!)
# git add ...
# git commit -m "Add haiku generator narrative tool"
# git push origin feature/haiku-generator
```

### 4. Test with Agent

```python
# Try via Python REPL
from src.agent.graph import create_agent

agent = create_agent()
response = agent.invoke({
    "query": "Write a haiku about forest loss in Paraná in October"
})

print(response)
```

---

## 📚 Dependencies to Add

Add to `pyproject.toml`:

```toml
[project.dependencies]
# ... existing dependencies ...

# For haiku syllable counting
pyphen = "^0.14.0"

# For soundscape generation (later)
pydub = "^0.25.1"
librosa = "^0.10.1"

# For image generation (later, optional)
# replicate = "^0.20.0"  # or other image API client
```

---

## 🎯 Success Criteria

**Week 1-2: Understanding**
- ✅ Can run project-zeno locally
- ✅ Understand agent → tools → LLM flow
- ✅ Know where to add new tools
- ✅ Can write tests matching their patterns

**Week 3-4: First Tool**
- ✅ Haiku generator works standalone
- ✅ Integrated with agent
- ✅ Tests passing (>80% coverage)
- ✅ Documentation complete

**Week 5-6: Second Tool**
- ✅ Added soundscape generator
- ✅ Demonstrated value with examples
- ✅ Shared in project-zeno discussions

**Week 7+: Community**
- ✅ Blog post about narrative experiments
- ✅ Engagement with upstream maintainers
- ✅ At least 1 tool considered for contribution

---

## 💡 Tips & Gotchas

**Do:**
- ✅ Follow their code style exactly (use `ruff` linter)
- ✅ Reuse their LLM clients (don't duplicate setup)
- ✅ Test both standalone and agent integration
- ✅ Document with examples
- ✅ Keep narrative tools in separate module

**Don't:**
- ❌ Modify their core agent code (extend, don't alter)
- ❌ Add heavy dependencies without discussion
- ❌ Skip tests ("it's just experimental")
- ❌ Commit directly to main branch
- ❌ Open upstream PR without prior discussion

**When Stuck:**
- 📖 Read their existing tool implementations as examples
- 💬 Ask in their GitHub Discussions
- 🔍 Search their issues for similar questions
- 📝 Document the problem (helps thinking)

---

## 🔗 Key Links

**Upstream:**
- Repo: https://github.com/wri/project-zeno
- API Docs: https://api.globalnaturewatch.org/docs
- Global Nature Watch: https://globalnaturewatch.org

**Our Documentation:**
- Full Copilot Instructions: `/docs/project-zeno-fork-copilot-instructions.md`
- ADR-001 (Fork Decision): `/docs/adr/ADR-001-real-time-forest-change-detection.md`
- Yuzu Methodology: `/docs/methodology.md`

**Technologies:**
- LangGraph: https://langchain-ai.github.io/langgraph/
- FastAPI: https://fastapi.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/

---

## ❓ FAQ

**Q: Should I fork or clone project-zeno?**  
A: Fork on GitHub, then clone your fork. This allows you to push changes and potentially open PRs.

**Q: How do I sync with upstream?**  
A: Regularly `git fetch upstream && git merge upstream/main`.

**Q: Can I modify their core code?**  
A: Avoid it. Extend with new modules. If you find a bug, open an issue first.

**Q: Which tool should I build first?**  
A: Haiku Generator — simplest to implement, proves the pattern.

**Q: How do I know if my tool is good enough for upstream?**  
A: If it's well-tested, documented, and solves a general problem (not just your niche), discuss it with maintainers.

**Q: What if my narrative tool needs large dependencies?**  
A: Make them optional or build as separate service with API integration.

---

**Last Updated:** 2025-11-05  
**Next Review:** After building first tool (Week 4)

