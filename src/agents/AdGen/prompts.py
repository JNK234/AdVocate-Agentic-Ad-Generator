from langchain.prompts import ChatPromptTemplate

STRATEGY_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert advertising strategist. Analyze the provided brand information, target audience, and campaign goals to develop a comprehensive strategy analysis."""),
    ("human", """Please analyze the following campaign elements:
    Brand Information: {brand_info}
    Target Audience: {target_audience}
    Campaign Goals: {campaign_goals}
    
    Provide a strategic analysis that will guide creative direction."""),
])

CREATIVE_DIRECTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a creative director specializing in advertising campaigns. Generate creative direction based on the strategy analysis."""),
    ("human", """Based on the following strategy analysis:
    {strategy_analysis}
    
    Generate creative direction including visual themes, messaging tone, and key elements to incorporate."""),
])

TAGLINE_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a copywriter specializing in creating impactful advertising taglines."""),
    ("human", """Create a tagline based on:
    Core Message: {core_message}
    Visual Theme: {visual_theme}
    Emotional Appeal: {emotional_appeal}
    
    Generate a memorable and impactful tagline."""),
])

STORY_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a narrative expert specializing in brand storytelling."""),
    ("human", """Create a compelling story based on:
    Core Message: {core_message}
    Visual Theme: {visual_theme}
    Emotional Appeal: {emotional_appeal}
    
    Generate an engaging narrative that resonates with the target audience."""),
])

IMAGE_PROMPT_GENERATION = ChatPromptTemplate.from_messages([
    ("system", """You are an art director specializing in visual advertising concepts. Create concise, impactful image prompts that capture the essence of advertising campaigns while staying under 2000 characters. Focus on key visual elements and keep descriptions clear and specific."""),
    ("human", """Generate a focused image prompt based on:
    Core Message: {summary_prompt}
    
    Additional Context:
    - Product Details: {product_prompt}
    - Brand Elements: {brand_prompt}
    - Social Context: {social_prompt}
    
    Create a concise prompt (under 2000 characters) that emphasizes the core message while incorporating key visual elements. Focus on the most impactful aspects that will create compelling advertising imagery."""),
])

QUALITY_CHECK_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a quality assurance specialist for advertising campaigns."""),
    ("human", """Review the following campaign assets:
    Tagline: {tagline}
    Story: {story}
    Image Prompt: {image_prompt}
    
    Evaluate the assets for consistency, impact, and alignment with campaign goals."""),
])
