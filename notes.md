#### AI-Powered Cold Email / LinkedIn Message Generator for Job Opportunities

1. **Overview**

**Objective:**

- Build an AI-powered system to generate personalized cold emails tailored for job opportunities.
- focus on creating genuine connections, showcasing interest, and standing out from generic templates.
  Target Users:
  • Job Seekers (entry-level to executive roles)
  • Freelancers and Consultants

1. **Problem Statement**
   • Generic cold emails often fail to grab attention.
   • Job seekers struggle to write engaging and customized emails when asking for referrals or sending ice breaker mails for value proposition w.r.t their relevant desired roles.
   • Lack of personalization reduces email response rates ( although there are several other factors that come into play here as well, like email classified as spam or not-spam, org level restrictions )
   • Many tools generate templated and impersonal emails.
2. **Goals and Objectives**
   • Create highly personalized cold emails tailored to specific job roles and recipients.
   • Include icebreakers based on public data (e.g., LinkedIn, company websites or recent news about the company, problems the company is trying to solve ).
   • Enable customization for tone, style, and email length.
   • Provide actionable insights for follow-ups.
3. **Key Features**

4.1 User Input Section:
 • Job Role & Company Name: Role user is applying for and the company name.
 • Recipient’s Name & Designation: Personalized details of the recipient.
 • LinkedIn Profile URL / Website: Used for context extraction.
 • Specific Interests/Points to Highlight: Any personal connection or shared interest.
 • Tone Selector: Friendly, Formal, Confident, Enthusiastic.

4.2 AI-Generated Output:
 • Generate a strong email subject line.
 • Provide an attention-grabbing icebreaker sentence.
 • Create a 3-5 sentence body focused on personalization and value proposition.
 • Include a clear call-to-action (CTA).

4.3 Enhanced Personalization:
 • Fetch public information (e.g., recent LinkedIn posts, achievements, blogs).
 • Reference shared connections or events.
 • Suggest unique conversation starters.

4.4 Templates and Iterations:
 • Allow users to generate multiple variations of an email.
 • Save preferred versions and compare drafts.

4.5 Follow-up Email Suggestions:
 • Provide suggestions for follow-up emails after no response.
 • Automate polite nudges.

5. **Data Requirements**

5.1 User-Provided Data:
 • Recipient’s name, job title, company name.
 • LinkedIn profile URL.
 • Any additional personal details or achievements.

5.2 Contextual Data (Extracted via Scrapers/APIs):
 • Public LinkedIn profile data (recent posts, job role, mutual connections).
 • Company details (mission, recent news, key achievements).
 • Relevant skills and keywords from the job description.

1. Workflow

   1. User Inputs Details: Job role, recipient details, LinkedIn URL, custom points.
   2. Context Extraction: Fetch public details (LinkedIn posts, recent achievements).
   3. Content Generation: LLM generates a tailored email with:
      • Icebreaker referencing extracted context.
      • Personalized email body.
      • Clear CTA.
   4. Review & Customize: User reviews the draft version, refines it (if needed, human-in-the-loop feedback mechanism ).
   5. Send & Analyze (Optional): Integration with email platforms (e.g., Gmail, Outlook).
2. Personalization Techniques
   • Contextual Hooks: Reference recipient’s recent LinkedIn post or shared interest.
   • Emotion Mapping: Detect the tone from public posts and mirror it in the email.
   • Adaptive Writing Style: Adjust tone based on job role (e.g., casual for startups, formal for corporates).
   • Dynamic Variables: Insert custom tokens like {Recipient_Name}, {Company_Name}, {Recent_Achievement}.
3. Competitive Edge
   • Deeper Personalization: Move beyond templates; use public data for meaningful connections.
   • Tone Customization: Adapt tone based on user preference.
   • Follow-up Automation: Generate follow-up sequences without sounding repetitive.
   • Scalability: Capable of handling bulk email personalization for campaigns.
4. Success Metrics
    • Average response rate of generated emails.
    • User retention rate (repeat usage).
    • User satisfaction feedback.
    • Number of personalized drafts generated per session.
5. Future Enhancements
    • Integration with CRM platforms (e.g., HubSpot, Salesforce).
    • AI voice-based cold calls using speech models.
    • Email success predictor (predict likelihood of response).
6. Challenges and Risks
    • Data Privacy Concerns: Ensure compliance with GDPR and data security regulations.
    • LinkedIn API Limitations: Manage rate limits and potential scraping restrictions.
    • Avoiding Over-Personalization: Maintain professionalism without being overly intrusive.

#### Solution Approach

1. input from the user --> cv pdf, desired job title ( optional - if not provided the agent will identify a pool of best suited job titles corresponding to the candidate resume ), target company type (optional, if not provided no preference, serve what u get from the web) --> start ups or mnc or t-1 vc firm backed companies like yc companies, accel, sequoia
2. Parse the pdf, use structured parsing (maybe llamaparse ? or docling ?? dk, will decide) and store the candidate info in a db with fixed attributes
  - For now, using `llamaparse` but docling is also getting better so can add it in fallback maybe post testing -- NOTE
- prepare an exhaustive list of job titles for the user to select from or the user can enter manually.
3. identify the job titles / job roles for which candidate is a top applicant ( max 3 ) -- optional ( will look later into it )
4. fetch job postings in structured format based on company type and location:
   - define a deterministic workflow for now
     - if company type is mncs or enterprise, use a set of predefined company job board urls to fetch the data
     - if company type is startup, use yc and wellfound job board urls, for yc we need serp + scrape and for wellfound we need 2 levels of scraping --> maybe i can check here if compositional function calling can handle this use case or like sequential function calling ????
     - if any is used, then use some default common job boards like linkedin, naukri, indeed, google jobs
5. fetch 5 HR contacts and 5 contacts with senior designation corresponding to the applicant job role
6. fetch relevant company initiatives, pain points if any, events or news in correspondence to the applicant's profile ( basically how your skills and experience can add value to their product / services )
7. generate personalized outreach cold emails
8. serve the system as a cli tool ?
   - why not an API ?
     - API gateway timeout error chance.
     - bad user experience, until the response is generated completely, user is in a waiting state
     - request-response model are atomic in nature -->
       - can send partial response as well by handling exceptions efficiently but not reliable

- user input :
  - user portfolio / resume
    - start with user resume and extend it to user github and portfolio website or user linkedin
  - target job role
  - user's current YOE ( int )
  - target list of companies
- output : list of personalized email drafts
- take the user input and identify relevant job roles from the target companies' career pages
  - how to do this ?
    - use web search + scraping with firecrawl
      - search query : {company name} careers
  - filter the search results to fetch the relevant
- extract job details from the apply links
- match jobs to your resume and filter out the most relevant job roles along with their company
- identify potential contacts to which the applicant can reach out considering the following signals in the target company contacts:
  - Role relevance to applicant's career goals
  - Hiring authority level
  - Activity status (recent posts/engagement)
  - Shared backgrounds
  - Engagement history with similar outreach

#### Note

optimal outreach email length for job opportunities should be:

150-200 words (3-4 short paragraphs) structured as follows:

1. Opening (30-40 words)

- Brief personal introduction
- Specific connection point or shared interest
- Clear purpose statement

2. Value Proposition (50-60 words)

- 1-2 relevant achievements/skills
- Direct link to company's needs/goals
- Brief mention of why this company specifically

3. Call to Action (30-40 words)

- Clear, specific request
- Suggested next step
- Flexibility in timing

4. Closing (<20 words)

- Brief appreciation
- Professional sign-off
- Full signature with contact details

## email generation service
input required:
- sender / job seeker info: parsed resume, linkedin scraped data ( optional ), github scraping to get the idea of real world projects build by the job seeker
- receiver info : reciever full name or first name (if full name is not available), reciever job title ( optional maybe for now i dont need this info ? )
- job opening details
- company recent news or insights (sometimes, the roles and responsibilities give an idea about the team and the problem statement the team is solving)

create 2 sample input json files, using 2 resumes and 2 job roles: mle and swe
