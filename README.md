# 🚀 Icebreaker AI

**AI-Powered Job Search & Personalized Outreach Platform**

Transform your job search with intelligent resume parsing, job matching, and personalized cold email generation.

## 🎯 **Core Value Proposition**

Icebreaker AI eliminates the manual grind of job searching by automatically:
- **Parsing your resume** into structured data
- **Finding relevant job opportunities** across multiple platforms
- **Generating personalized cold emails & LinkedIn messages** that actually get responses
- **Matching you with the right contacts** at target companies

## 🔥 **Key Features**

### 📄 **Smart Resume Parsing**
- Extract structured data from PDF resumes using LlamaParse
- Identify skills, experience, and achievements automatically
- Store candidate profiles in database for quick access

### 🎯 **Intelligent Job Matching**
- Parse job postings from company career pages
- Match candidate skills with job requirements
- Filter opportunities by company type (Startup, Enterprise, YC-backed)
- Recommend top 3 most relevant job roles

### 📧 **Personalized Email Generation**
- **3 Email Types**: Simple, Personalized, Contextual
- **4 Customizable Tones**: Formal, Friendly, Concise, Enthusiastic
- **AI-Powered Personalization**: Skills matching, experience highlighting
- **Contextual Hooks**: Company news, recent achievements, shared interests

### 🔍 **Intelligent Personalized Contact Discovery**
- Find HR contacts and senior professionals at target companies
- Identify hiring managers and decision-makers
- Filter by role relevance and activity level

## 🏗️ **Architecture**

```
Resume Upload → Parse & Store → Job Matching → Contact Discovery → Email Generation → Outreach
```

### **Tech Stack**
- **Backend**: FastAPI, Python 3.12+
- **AI/ML**: LangChain, LangGraph, Anthropic Claude, Google Gemini
- **Data Processing**: LlamaParse, Firecrawl
- **Database**: SQLite (async)
- **Workflow**: LangGraph for state management


### **Prerequisites**
```bash
# Install dependencies
poetry install

# Set environment variables
export ANTHROPIC_API_KEY="your_key"
export LLAMA_CLOUD_API_KEY="your_key"
export FIRECRAWL_API_KEY="your_key"
export GEMINI_API_KEY="your_key"
```

## 🎨 **Email Types & Tones**

### **Email Types**
1. **Simple** - Basic template with essential info
2. **Personalized** - Skills matching and experience highlights
3. **Contextual** - External data integration (GitHub, company news, LinkedIn)

### **Tone Options**
- **Formal** - Professional and business-like
- **Friendly** - Warm and approachable  
- **Concise** - Brief and to-the-point
- **Enthusiastic** - Energetic and passionate

## 🔧 **Advanced Features**

### **External Data Integration**
- **GitHub**: User repos, activity, contributions
- **Company News**: Recent updates, tech announcements
- **LinkedIn**: Company updates, shared connections
- **Web Scraping**: Company website information

### **Workflow Management**
- **LangGraph**: Structured state management
- **Async Processing**: Concurrent data fetching
- **Error Handling**: Robust fallback mechanisms
- **Extensible**: Easy to add new data sources

## 📈 **Success Metrics**

- **Response Rate**: Track email engagement
- **Job Match Quality**: Relevance scoring
- **User Retention**: Repeat usage patterns
- **Email Effectiveness**: A/B testing capabilities

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

**Built with ❤️ for job seekers who want to stand out** 