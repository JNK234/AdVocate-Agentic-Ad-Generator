from langchain.prompts.chat import ChatPromptTemplate

CAMPAIGN_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a creative marketing director tasked with generating innovative advertising campaign ideas. 
You will be provided with company information, the target audience, and brand values. Use this information to generate 5 distinct campaign ideas.

Company Information:
{company_summary}

Target Audience:
{target_audience}

Brand Values:
{brand_values}

For each campaign idea, provide:
1. Campaign Name: A memorable and distinctive title that captures the essence of the campaign.
2. Core Message: The primary value proposition or key takeaway for the audience.
3. Visual Theme Description: A detailed description of the campaign's visual style, including color palette suggestions, photography/illustration style, key visual elements, mood, and atmosphere.
4. Key Emotional Appeal: The primary emotional response the campaign aims to evoke, including the primary emotion, supporting psychological triggers, and desired audience reaction.
5. Social Media Focus: A platform-specific strategy, including primary platforms (e.g., Instagram, LinkedIn, TikTok), content format recommendations, engagement tactics, and hashtag strategy.
6. Campaign Timeline: A suggested campaign duration and key phases.
7. Success Metrics: Specific KPIs and measurement criteria.
8. Budget Allocation: Recommended distribution across channels.
9. Risk Mitigation: Potential challenges and mitigation strategies.

Each campaign should:
- Resonate with the target audience.
- Maintain brand consistency.
- Have a unique angle and visual style.
- Align with the brand values and target audience preferences.

Consider these aspects for each campaign:
- Cultural relevance and sensitivity.
- Cross-platform integration possibilities.
- Viral potential and shareability.
- Long-term brand building potential.
- Measurable business impact.

Format each campaign as a structured output with clear sections and detailed subsections."""),
    ("user", "Generate 5 campaign ideas based on the company information, target audience, and brand values provided."),
])
