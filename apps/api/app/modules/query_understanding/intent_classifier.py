"""Rule-based multi-label legal intent classification."""

from __future__ import annotations

from app.modules.query_understanding.normalizer import fold_text, normalize_query

INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "definition": ("la gi", "duoc hieu la", "dinh nghia", "giai thich tu ngu"),
    "scope": ("pham vi", "doi tuong ap dung", "dieu chinh", "loai tru", "khong dieu chinh"),
    "prohibition": ("bi cam", "nghiem cam", "co duoc", "khong duoc", "cam khong"),
    "condition": ("dieu kien", "can dap ung", "co phai", "duoc phep", "yeu cau nao"),
    "authority": ("co quan nao", "tham quyen", "ai cap", "uy ban", "bo nao", "toa an nao"),
    "procedure": ("thu tuc", "trinh tu", "ho so", "nop", "tiep nhan", "giai quyet nhu the nao"),
    "deadline": ("bao lau", "thoi han", "trong bao nhieu", "ngay lam viec", "truoc bao lau"),
    "rights_obligations": ("quyen", "nghia vu", "trach nhiem", "phai lam gi", "duoc lam gi"),
    "comparison": ("khac nhau", "so sanh", "phan biet", "giong nhau"),
    "penalty": ("xu phat", "truy cuu", "boi thuong thiet hai", "trach nhiem phap ly"),
}


class IntentClassifier:
    """Classify legal question intents with simple keyword rules."""

    def classify(self, query: str) -> list[str]:
        folded = fold_text(normalize_query(query))
        intents = [intent for intent, keywords in INTENT_KEYWORDS.items() if any(keyword in folded for keyword in keywords)]
        return intents or ["general"]
