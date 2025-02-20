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
    ("system", """You are an art director specializing in visual advertising concepts."""),
    ("human", """Create an image generation prompt based on:
    Campaign Name: {campaign_name}
    Product Focus: {product_prompt}
    Brand Elements: {brand_prompt}
    Social Media Context: {social_prompt}
    
    Generate a detailed prompt that will create visually compelling advertising imagery."""),
])

QUALITY_CHECK_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a quality assurance specialist for advertising campaigns."""),
    ("human", """Review the following campaign assets:
    Tagline: {tagline}
    Story: {story}
    Image Prompt: {image_prompt}
    
    Evaluate the assets for consistency, impact, and alignment with campaign goals."""),
])
