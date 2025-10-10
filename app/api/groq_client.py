import os
import re
import json
import requests
import logging
import re
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

def analyze_resume_with_groq(resume_text: str, job_description: str) -> dict:

    if not GROQ_API_KEY:
     raise RuntimeError("GROQ_API_KEY not set in environment")
    """
    Sends resume and JD to Groq API and extracts structured insights.
    Always returns a dict with keys: score, missing_keywords, suggestions.
    """
    # resume_keyword = extract_jd_keywords(resume_text)
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "temperature": 0,
        "response_format": { "type": "json_object" },
        "messages": [
            {
               "role": "system",
    "content": """
     INPUT FORMAT
----------
The assistant will receive two raw text blobs. They will be injected below between the markers.
You MUST parse them and return ONLY the JSON object in the exact schema described afterwards.

###JOB_DESCRIPTION_START###
{JOB_DESCRIPTION_HERE}
###JOB_DESCRIPTION_END###

###RESUME_START###
{RESUME_HERE}
###RESUME_END###

OUTPUT SCHEMA (MUST be the ONLY CONTENT RETURNED)
{
  "ats_score": <integer 0-100>,
  "keyword_match_score": <integer 0-100>,
  "missing_keywords": [<list of strings>],
  "suggestions": [<list of strings>]
}

DETERMINISTIC RULES & MATCHING ALGORITHM (follow exactly)
1. Normalization:
   - Convert both JD and Resume to lowercase.
   - Strip punctuation except characters used in tech names (+, #, ., -), e.g. keep "c++", "node.js", "c#".
   - Collapse multiple spaces.
2. Keyword extraction (from JD):
   - Extract explicit terms, lists, comma-separated skills, quoted tokens, parenthesized items, and capitalized multi-word phrases.
   - Include: hard skills, soft skills, technologies, protocols, minimum experience phrasing (e.g. "5+ years"), education requirements phrasing(e.g. Bachelor’s Degree or equivalent in Computer Science, Software Engineering, or related field.), role names.
   - Produce a deduplicated list. Order does not matter.
   - DO NOT invent keywords not present (no summarization).
3. Matching rules (deterministic):
   - For each JD keyword (as an exact phrase), create a normalized form and compare to resume text using these checks in order:
     a) Exact phrase present → full match weight = 1.0
     b) Token subset: all tokens of the JD keyword appear in resume (anywhere) → full match weight = 1.0
     c) Partial token overlap ≥ 60% → partial match weight = 0.5
     d) Synonym mapping: consult the built-in synonym map (below) — if present in resume, treat as partial match weight = 0.5 (only if not matched by a/b/c).
     e) Otherwise not matched (weight = 0).
   - Synonym map (apply these as deterministic examples; add others only when exact lexical variants are obvious):
     { "js": "javascript", "node": "node.js", "reactjs": "react", "aws": "amazon web services", "postgres": "postgresql", "sql": "sql", "csharp": "c#", "cpp": "c++" }
4. keyword_match_score:
   - Compute sum_of_weights = Σ(weight for each JD keyword).
   - score = floor( (sum_of_weights / total_number_of_jd_keywords) * 100 ).
   - If JD has 0 extracted keywords, set keyword_match_score = 0.
5. ats_score:
   - Compute resume_quality (0-100) from these conservative heuristics (model must be conservative):
     • Experience-level match (seniority & years): 0-30 (give full points only if explicit years and seniority match or exceed JD request)
     • Education & required credentials: 0-20
     • Formatting & clarity (presence of bullets, clear sections for experience/skills): 0-20
     • Relevance of job titles & achievements (metrics present): 0-30
   - Then combine: ats_score = floor( 0.7 * keyword_match_score + 0.3 * resume_quality ).
6. missing_keywords:
   - Return Missing JD Keywords that the hiring manager or recruiter would spot out and care about.
   - Return every JD keyword whose final match weight == 0. Order can be any.
   - If all keywords matched (sum_of_weights equals total JD keywords), return [].
7. suggestions:
   - Return suggestions that an hiring manager or recruiter would give to improve the resume.
   - Return 5–10 short (max 120 characters each) actionable suggestions in plain English.
   - Keep them conservative and specific (e.g., "Add 'Spring Boot' to skills if you have experience", "Quantify achievements with numbers", "Match job title to JD").
8. Output requirements:
   - All numbers must be integers.
   - JSON only. No extra keys. No debugging fields.
   - Deterministic: use exact algorithm above (temperature=0 recommended).
Now produce the JSON using the provided JD and Resume above.

    """
          },

            {
                "role": "user",
                "content": f"""
          Job Description:
          {job_description}

          Resume:
          {resume_text}
          """
            },
        ],
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"].strip()

        # Extract JSON safely
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group())

    except Exception as e:
     logger.error(f"Groq API call failed: {e}")
     return {
          "ats_score": 0,
          "keyword_match_score": 0,
          "missing_keywords": [],
          "suggestions": [f"Groq API failed: {str(e)}"]
     }



def extract_resume_json_with_groq(resume_text: str) -> dict:
    """
    Dynamically extract and structure a resume into universal 'Classic' JSON.
    Works across any profession — AI determines section names and order.
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set in environment")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": """
You are an advanced resume parser that converts *any unstructured resume text* (from any profession or region) into a standardized, universal JSON structure usable for classic resume templates and ATS systems."

### OUTPUT FORMAT (VALID JSON ONLY)
{
  "sections": {
    "Header": {
      "fullName": string,
      "title": string (optional),
      "email": string,
      "phone": string (optional),
      "location": string (optional),
      "linkedin": string (optional),
      "website": string (optional)
    },

    "Professional Summary": string (optional),

    "Skills": {
      "<category>": [string]
    },

    "Work Experience": [
      {
        "role": string,
        "company": string,
        "location": string (optional),
        "startDate": string (optional),
        "endDate": string (optional),
        "achievements": [string]
      }
    ],

    "Projects": [
      {
        "name": string,
        "achievements": [string],
        "techStack": [string] (optional)
      }
    ],

    "Education": [
      {
        "institution": string,
        "degree": string (optional),
        "location": string (optional),
        "startDate": string (optional),
        "endDate": string (optional)
      }
    ],

    "Certifications": [string] (optional),
    "Awards": [string] (optional),
    "Publications": [string] (optional),
    "Languages": [string] (optional),
    "Volunteer Experience": [object] (optional),
    "Memberships": [string] (optional),
    "References": [string] (optional)
  },

  "order": [string]  // ordered list of section names (AI decides based on relevance)
}

### RULES:
1. Works for *any* profession: engineering, healthcare, finance, law, education, design, etc.
2. Detect and create skill categories dynamically (e.g., “Clinical”, “Finance & Accounting”, “Software Development”, “Communication”, “Leadership”).
3. NEVER group everything under “Others”. If skills span domains, create multiple logical categories.
4. Extract **real content only** — no invented details.
5. Keep text concise, clean, and professional.
6. Preserve logical order of sections as they appear or make sense for the profession.
7. Always output **valid JSON** — no markdown or extra commentary.
8. Limit the text to ~2 pages’ worth of content.
9. If a section is missing, omit it from the "sections" object.
10. Never return empty section (e.g, if there us certifications in the section list and it has no data under it).
"""
            },
            {"role": "user", "content": resume_text}
        ],
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise ValueError("Groq did not return valid JSON")

        parsed = json.loads(match.group())

        # Safety defaults
        parsed.setdefault("sections", {})
        parsed.setdefault("order", list(parsed["sections"].keys()))

        return parsed

    except Exception as e:
        logger.error(f"Groq universal resume parse failed: {e}")
        return {"sections": {}, "order": []}






def normalize_date(value: str) -> str:
    """
    Normalize date strings to YYYY-MM or 'Present'.
    Rules:
    - "Present" stays as is.
    - "2020" → "2020-01"
    - "May 2025", "May2025", "05/2025", "2025/05" → "2025-05"
    - Unknown/unparseable → ""
    """
    if not value:
        return ""
    
    value = value.strip()

    # Keep Present
    if re.search(r'present', value, re.IGNORECASE):
        return "Present"

    # Year only
    year_match = re.fullmatch(r'(\d{4})', value)
    if year_match:
        return f"{year_match.group(1)}-01"

    # Month + Year (e.g., "May 2025" or "May2025")
    month_map = {
        "jan": "01", "january": "01",
        "feb": "02", "february": "02",
        "mar": "03", "march": "03",
        "apr": "04", "april": "04",
        "may": "05",
        "jun": "06", "june": "06",
        "jul": "07", "july": "07",
        "aug": "08", "august": "08",
        "sep": "09", "sept": "09", "september": "09",
        "oct": "10", "october": "10",
        "nov": "11", "november": "11",
        "dec": "12", "december": "12",
    }
    month_year = re.match(r'([A-Za-z]+)\s?(\d{4})', value)
    if month_year:
        month_str, year = month_year.groups()
        month = month_map.get(month_str.lower()[:3])
        if month:
            return f"{year}-{month}"

    # Formats like 05/2025 or 2025/05
    slash_match = re.match(r'(\d{1,2})[/-](\d{4})', value)
    if slash_match:
        m, y = slash_match.groups()
        return f"{y}-{int(m):02d}"
    slash_match2 = re.match(r'(\d{4})[/-](\d{1,2})', value)
    if slash_match2:
        y, m = slash_match2.groups()
        return f"{y}-{int(m):02d}"

    # Already ISO
    iso_match = re.match(r'(\d{4})-(\d{2})', value)
    if iso_match:
        return value

    return ""  # Fallback if nonsense


def clean_resume_json(resume_json: dict) -> dict:
    """
    Walk the ResumeData JSON and normalize all date fields.
    """
    for exp in resume_json.get("experience", []):
        exp["startDate"] = normalize_date(exp.get("startDate", ""))
        exp["endDate"] = normalize_date(exp.get("endDate", ""))

    for edu in resume_json.get("education", []):
        edu["startDate"] = normalize_date(edu.get("startDate", ""))
        edu["endDate"] = normalize_date(edu.get("endDate", ""))

    return resume_json
