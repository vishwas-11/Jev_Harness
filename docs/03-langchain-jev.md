# LangChain Jev integration boundary

Phase 1 does not make provider calls. Phase 3 will verify the installed package against the current official integration before implementing the adapter.

```python
from langchain_typesafe import Choice, Noul, Score, TypeSafeClassifier

classifier = TypeSafeClassifier()
response = classifier.invoke({
    "state": email_text,
    "questions": {
        "intent": Choice(instructions="...", criteria={"billing": "..."}),
        "urgency": Score(instructions="...", criteria=["low", "high"]),
        "spam": Noul(instructions="Is this spam?"),
    },
})
```

The final implementation will use one Jev invocation containing all enabled questions for an email where supported and preserve raw provider response metadata for traceability.

