"""In-memory mock CRM customer dataset (≥25 records)."""

from __future__ import annotations

from datetime import datetime, timezone

from crm_api.customers.schemas import CustomerComment, CustomerDetail

_UTC = timezone.utc


def _dt(year: int, month: int, day: int, hour: int = 10, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=_UTC)


_RAW: list[dict] = [
  {"id": "cust-001", "name": "Alice Morgan", "email": "alice.morgan@northwind.io", "company": "Northwind Labs", "country": "United States", "state": "CA", "status": "Lead", "warmStatus": "Hot", "inclusionDate": _dt(2024, 1, 12), "lastCommunicationDate": _dt(2025, 5, 2, 14, 30), "phone": "+1 415-555-0101", "segment": "Enterprise", "accountOwner": "Jordan Lee", "leadSource": "Webinar", "comments": [{"id": "c-001", "text": "Interested in annual contract.", "author": "Jordan Lee", "createdAt": _dt(2025, 4, 28, 9, 0)}]},
  {"id": "cust-002", "name": "Bruno Ferreira", "email": "bruno.ferreira@acme.com.br", "company": "Acme Brasil", "country": "Brazil", "state": "SP", "status": "Prospect", "warmStatus": "Warm", "inclusionDate": _dt(2024, 3, 5), "lastCommunicationDate": _dt(2025, 4, 18, 11, 15), "phone": "+55 11 95555-0202", "segment": "Mid-Market", "accountOwner": "Ana Costa", "leadSource": "Referral", "comments": []},
  {"id": "cust-003", "name": "Carlos Vega", "email": "c.vega@solartech.mx", "company": "SolarTech MX", "country": "Mexico", "state": "JAL", "status": "Active", "warmStatus": "Hot", "inclusionDate": _dt(2023, 11, 20), "lastCommunicationDate": _dt(2025, 5, 10, 16, 45), "phone": "+52 33 5555-0303", "segment": "Enterprise", "accountOwner": "Maria Gomez", "leadSource": "Trade Show", "comments": [{"id": "c-003", "text": "Renewal discussion scheduled.", "author": "Maria Gomez", "createdAt": _dt(2025, 5, 8, 10, 0)}]},
  {"id": "cust-004", "name": "Diana Chen", "email": "diana.chen@pacificdata.sg", "company": "Pacific Data", "country": "Singapore", "state": "—", "status": "Lead", "warmStatus": "Warm", "inclusionDate": _dt(2025, 2, 1), "lastCommunicationDate": None, "phone": "+65 6123 0404", "segment": "SMB", "accountOwner": "Ken Tan", "leadSource": "Inbound", "comments": []},
  {"id": "cust-005", "name": "Elena Rossi", "email": "elena.rossi@verde.it", "company": "Verde Systems", "country": "Italy", "state": "MI", "status": "Prospect", "warmStatus": "Hot", "inclusionDate": _dt(2024, 6, 14), "lastCommunicationDate": _dt(2025, 3, 22, 8, 20), "phone": "+39 02 5555-0505", "segment": "Mid-Market", "accountOwner": "Luca Bianchi", "leadSource": "Partner", "comments": []},
  {"id": "cust-006", "name": "Frank Okafor", "email": "f.okafor@lagosfin.ng", "company": "Lagos Fin", "country": "Nigeria", "state": "LA", "status": "Inactive", "warmStatus": "Warm", "inclusionDate": _dt(2022, 9, 9), "lastCommunicationDate": _dt(2024, 12, 1, 13, 0), "phone": "+234 803 555 0606", "segment": "SMB", "accountOwner": "Amina Bello", "leadSource": "Cold Call", "comments": [{"id": "c-006", "text": "Paused evaluation until Q3.", "author": "Amina Bello", "createdAt": _dt(2024, 11, 15, 15, 30)}]},
  {"id": "cust-007", "name": "Grace Kim", "email": "grace.kim@seoulwave.kr", "company": "Seoul Wave", "country": "South Korea", "state": "Seoul", "status": "Active", "warmStatus": "Hot", "inclusionDate": _dt(2023, 4, 2), "lastCommunicationDate": _dt(2025, 5, 11, 7, 50), "phone": "+82 2-555-0707", "segment": "Enterprise", "accountOwner": "Min Park", "leadSource": "Webinar", "comments": []},
  {"id": "cust-008", "name": "Hassan Al-Rashid", "email": "h.alrashid@gulfco.ae", "company": "Gulf Co", "country": "UAE", "state": "DU", "status": "Lead", "warmStatus": "Warm", "inclusionDate": _dt(2025, 1, 25), "lastCommunicationDate": _dt(2025, 2, 10, 12, 0), "phone": "+971 4 555 0808", "segment": "Mid-Market", "accountOwner": "Sara Nasser", "leadSource": "LinkedIn", "comments": []},
  {"id": "cust-009", "name": "Isabelle Dupont", "email": "isabelle.dupont@bleu.fr", "company": "Bleu Analytics", "country": "France", "state": "IDF", "status": "Prospect", "warmStatus": "Hot", "inclusionDate": _dt(2024, 8, 30), "lastCommunicationDate": _dt(2025, 4, 5, 17, 10), "phone": "+33 1 55 55 09 09", "segment": "Enterprise", "accountOwner": "Pierre Martin", "leadSource": "Inbound", "comments": []},
  {"id": "cust-010", "name": "James Wilson", "email": "james.wilson@maple.ca", "company": "Maple Digital", "country": "Canada", "state": "ON", "status": "Active", "warmStatus": "Warm", "inclusionDate": _dt(2023, 7, 19), "lastCommunicationDate": _dt(2025, 5, 9, 9, 30), "phone": "+1 416-555-1010", "segment": "Mid-Market", "accountOwner": "Emily Clark", "leadSource": "Referral", "comments": []},
  {"id": "cust-011", "name": "Keiko Tanaka", "email": "keiko.tanaka@tokyoedge.jp", "company": "Tokyo Edge", "country": "Japan", "state": "Tokyo", "status": "Lead", "warmStatus": "Hot", "inclusionDate": _dt(2025, 3, 3), "lastCommunicationDate": None, "phone": "+81 3-5555-1111", "segment": "SMB", "accountOwner": "Yuki Sato", "leadSource": "Webinar", "comments": []},
  {"id": "cust-012", "name": "Liam O'Brien", "email": "liam.obrien@emerald.ie", "company": "Emerald SaaS", "country": "Ireland", "state": "D", "status": "Prospect", "warmStatus": "Warm", "inclusionDate": _dt(2024, 5, 11), "lastCommunicationDate": _dt(2025, 1, 20, 14, 0), "phone": "+353 1 555 1212", "segment": "SMB", "accountOwner": "Niamh Walsh", "leadSource": "Partner", "comments": []},
  {"id": "cust-013", "name": "Marta Silva", "email": "marta.silva@atlantic.pt", "company": "Atlantic Cloud", "country": "Portugal", "state": "Lisbon", "status": "Active", "warmStatus": "Hot", "inclusionDate": _dt(2022, 12, 1), "lastCommunicationDate": _dt(2025, 5, 7, 18, 25), "phone": "+351 21 555 1313", "segment": "Enterprise", "accountOwner": "Rui Pereira", "leadSource": "Trade Show", "comments": [{"id": "c-013", "text": "Expansion to 3 subsidiaries.", "author": "Rui Pereira", "createdAt": _dt(2025, 5, 6, 11, 0)}]},
  {"id": "cust-014", "name": "Noah Schmidt", "email": "noah.schmidt@alpen.de", "company": "Alpen Tech", "country": "Germany", "state": "BY", "status": "Inactive", "warmStatus": "Warm", "inclusionDate": _dt(2021, 6, 6), "lastCommunicationDate": _dt(2024, 8, 14, 10, 0), "phone": "+49 89 5555 1414", "segment": "Mid-Market", "accountOwner": "Hans Weber", "leadSource": "Cold Call", "comments": []},
  {"id": "cust-015", "name": "Olivia Brown", "email": "olivia.brown@harbor.au", "company": "Harbor Systems", "country": "Australia", "state": "NSW", "status": "Lead", "warmStatus": "Warm", "inclusionDate": _dt(2025, 4, 14), "lastCommunicationDate": _dt(2025, 4, 20, 16, 0), "phone": "+61 2 5555 1515", "segment": "SMB", "accountOwner": "Jack Miller", "leadSource": "Inbound", "comments": []},
  {"id": "cust-016", "name": "Paulo Mendes", "email": "paulo.mendes@rio.br", "company": "Rio Ventures", "country": "Brazil", "state": "RJ", "status": "Prospect", "warmStatus": "Hot", "inclusionDate": _dt(2024, 10, 8), "lastCommunicationDate": _dt(2025, 3, 30, 13, 45), "phone": "+55 21 95555-1616", "segment": "Mid-Market", "accountOwner": "Ana Costa", "leadSource": "Referral", "comments": []},
  {"id": "cust-017", "name": "Quinn Taylor", "email": "quinn.taylor@peak.us", "company": "Peak Analytics", "country": "United States", "state": "CO", "status": "Active", "warmStatus": "Hot", "inclusionDate": _dt(2023, 2, 17), "lastCommunicationDate": _dt(2025, 5, 12, 8, 0), "phone": "+1 303-555-1717", "segment": "Enterprise", "accountOwner": "Jordan Lee", "leadSource": "Webinar", "comments": []},
  {"id": "cust-018", "name": "Rita Novak", "email": "rita.novak@prague.cz", "company": "Prague Data", "country": "Czech Republic", "state": "Prague", "status": "Lead", "warmStatus": "Warm", "inclusionDate": _dt(2025, 2, 22), "lastCommunicationDate": None, "phone": "+420 255 555 181", "segment": "SMB", "accountOwner": "Eva Horak", "leadSource": "LinkedIn", "comments": []},
  {"id": "cust-019", "name": "Samuel Wright", "email": "samuel.wright@stone.uk", "company": "Stone Retail", "country": "United Kingdom", "state": "ENG", "status": "Prospect", "warmStatus": "Warm", "inclusionDate": _dt(2024, 7, 4), "lastCommunicationDate": _dt(2025, 2, 28, 11, 30), "phone": "+44 20 5555 1919", "segment": "Mid-Market", "accountOwner": "Oliver Green", "leadSource": "Partner", "comments": []},
  {"id": "cust-020", "name": "Tania Popescu", "email": "tania.popescu@carpath.ro", "company": "Carpath Software", "country": "Romania", "state": "B", "status": "Active", "warmStatus": "Hot", "inclusionDate": _dt(2023, 9, 13), "lastCommunicationDate": _dt(2025, 4, 29, 15, 20), "phone": "+40 21 555 2020", "segment": "SMB", "accountOwner": "Andrei Ionescu", "leadSource": "Inbound", "comments": []},
  {"id": "cust-021", "name": "Uma Patel", "email": "uma.patel@bengal.in", "company": "Bengal IT", "country": "India", "state": "KA", "status": "Lead", "warmStatus": "Hot", "inclusionDate": _dt(2025, 5, 1), "lastCommunicationDate": _dt(2025, 5, 3, 9, 15), "phone": "+91 80 5555 2121", "segment": "Mid-Market", "accountOwner": "Raj Sharma", "leadSource": "Webinar", "comments": []},
  {"id": "cust-022", "name": "Victor Larsen", "email": "victor.larsen@nordic.se", "company": "Nordic Ops", "country": "Sweden", "state": "Stockholm", "status": "Inactive", "warmStatus": "Warm", "inclusionDate": _dt(2020, 4, 4), "lastCommunicationDate": _dt(2024, 6, 6, 12, 0), "phone": "+46 8 555 2222", "segment": "Enterprise", "accountOwner": "Erik Johansson", "leadSource": "Cold Call", "comments": []},
  {"id": "cust-023", "name": "Wendy Hughes", "email": "wendy.hughes@clear.nz", "company": "Clear NZ", "country": "New Zealand", "state": "AUK", "status": "Prospect", "warmStatus": "Hot", "inclusionDate": _dt(2024, 12, 12), "lastCommunicationDate": _dt(2025, 4, 2, 10, 40), "phone": "+64 9 555 2323", "segment": "SMB", "accountOwner": "Tom Baker", "leadSource": "Referral", "comments": []},
  {"id": "cust-024", "name": "Xavier Morales", "email": "x.morales@andes.cl", "company": "Andes Logistics", "country": "Chile", "state": "RM", "status": "Active", "warmStatus": "Warm", "inclusionDate": _dt(2023, 1, 28), "lastCommunicationDate": _dt(2025, 5, 6, 14, 55), "phone": "+56 2 5555 2424", "segment": "Mid-Market", "accountOwner": "Camila Rojas", "leadSource": "Trade Show", "comments": []},
  {"id": "cust-025", "name": "Yuki Nakamura", "email": "yuki.nakamura@osaka.jp", "company": "Osaka Retail", "country": "Japan", "state": "Osaka", "status": "Lead", "warmStatus": "Warm", "inclusionDate": _dt(2025, 3, 18), "lastCommunicationDate": None, "phone": "+81 6-5555-2525", "segment": "SMB", "accountOwner": "Yuki Sato", "leadSource": "Inbound", "comments": []},
  {"id": "cust-026", "name": "Zoe Anderson", "email": "zoe.anderson@bright.us", "company": "Bright Health", "country": "United States", "state": "TX", "status": "Prospect", "warmStatus": "Hot", "inclusionDate": _dt(2024, 4, 21), "lastCommunicationDate": _dt(2025, 5, 1, 17, 0), "phone": "+1 512-555-2626", "segment": "Enterprise", "accountOwner": "Jordan Lee", "leadSource": "Partner", "comments": [{"id": "c-026", "text": "Security review in progress.", "author": "Jordan Lee", "createdAt": _dt(2025, 4, 30, 9, 0)}]},
  {"id": "cust-027", "name": "Amir Haddad", "email": "amir.haddad@levant.lb", "company": "Levant Group", "country": "Lebanon", "state": "Beirut", "status": "Lead", "warmStatus": "Hot", "inclusionDate": _dt(2025, 4, 30), "lastCommunicationDate": _dt(2025, 5, 11, 11, 0), "phone": "+961 1 555 272", "segment": "Mid-Market", "accountOwner": "Sara Nasser", "leadSource": "LinkedIn", "comments": []},
  {"id": "cust-028", "name": "Beatriz Luna", "email": "beatriz.luna@sol.ar", "company": "Sol Argentina", "country": "Argentina", "state": "BA", "status": "Active", "warmStatus": "Warm", "inclusionDate": _dt(2023, 8, 7), "lastCommunicationDate": _dt(2025, 4, 17, 19, 10), "phone": "+54 11 5555-2828", "segment": "SMB", "accountOwner": "Camila Rojas", "leadSource": "Webinar", "comments": []},
]


def _build_customer(raw: dict) -> CustomerDetail:
    comments = [
        CustomerComment(
            id=c["id"],
            text=c["text"],
            author=c["author"],
            createdAt=c["createdAt"],
        )
        for c in raw.get("comments", [])
    ]
    return CustomerDetail(
        id=raw["id"],
        name=raw["name"],
        email=raw["email"],
        company=raw["company"],
        country=raw["country"],
        state=raw["state"],
        status=raw["status"],
        warmStatus=raw["warmStatus"],
        inclusionDate=raw["inclusionDate"],
        lastCommunicationDate=raw.get("lastCommunicationDate"),
        phone=raw["phone"],
        segment=raw["segment"],
        accountOwner=raw["accountOwner"],
        leadSource=raw["leadSource"],
        comments=comments,
    )


MOCK_CUSTOMERS: list[CustomerDetail] = [_build_customer(row) for row in _RAW]
