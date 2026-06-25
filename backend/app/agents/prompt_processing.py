import re


class PromptProcessingAgent:
    FILLERS = {"please", "kindly", "can you", "could you", "show me", "tell me", "i want to", "i would like to"}

    def normalize(self, text: str) -> str:
        cleaned = text.strip().lower()
        cleaned = cleaned.replace("₹", "rs ").replace("â‚¹", "rs ")
        for filler in self.FILLERS:
            cleaned = cleaned.replace(filler, "")
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    def classify_intent(self, text: str) -> str:
        t = text.lower()
        if any(k in t for k in ["increase", "set ", "update "]):
            return "UPDATE"
        if any(k in t for k in ["delete", "remove"]):
            return "DELETE"
        if any(k in t for k in ["insert", "add new", "create new"]):
            return "INSERT"
        if any(k in t for k in ["average", "count", "sum", "top", "highest", "lowest", "group by", "total"]):
            return "AGGREGATE"
        if any(k in t for k in ["show", "list", "find", "display", "fetch", "get"]):
            return "SELECT"
        return "UNKNOWN"

