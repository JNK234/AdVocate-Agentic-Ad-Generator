from typing import List, Dict
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import logging
class CampaignIdeaGenerator:
    def __init__(self, llm=None, num_campaigns: int = 5):
        """
        Initialize the prompt generator.
        
        Args:
            llm: Language model instance (optional)
            num_campaigns: Number of campaign ideas to generate (default: 5)
        """
        self.llm = llm
        self.num_campaigns = max(1, min(num_campaigns, 10))  # Ensure between 1 and 10
        self._init_prompts()

    def _init_prompts(self):
        """Initialize prompt templates for campaign generation."""
        self.campaign_prompt = PromptTemplate(
            input_variables=["company_info", "target_audience", "brand_values", "num_campaigns"],
            template="""As a creative marketing director, generate {num_campaigns} unique and innovative advertising campaign ideas 
            for the following company:

            Company Information:
            {company_info}

            Target Audience:
            {target_audience}

            Brand Values:
            {brand_values}

            For each campaign idea, provide:
            1. Campaign Name: A memorable, distinctive title that captures the essence of the campaign
            2. Core Message: The primary value proposition or key takeaway for the audience
            3. Visual Theme Description: Detailed description of the campaign's visual style, including:
               - Color palette suggestions
               - Photography/illustration style
               - Key visual elements
               - Mood and atmosphere
            4. Key Emotional Appeal: The primary emotional response the campaign aims to evoke, including:
               - Primary emotion
               - Supporting psychological triggers
               - Desired audience reaction
            5. Social Media Focus: Platform-specific strategy, including:
               - Primary platforms (e.g., Instagram, LinkedIn, TikTok)
               - Content format recommendations
               - Engagement tactics
               - Hashtag strategy
            6. Campaign Timeline: Suggested campaign duration and key phases
            7. Success Metrics: Specific KPIs and measurement criteria
            8. Budget Allocation: Recommended distribution across channels
            9. Risk Mitigation: Potential challenges and mitigation strategies

            Generate 5 distinctly different campaign approaches that would resonate with the target audience while 
            maintaining brand consistency. Each campaign should have a unique angle and visual style, but all should 
            align with the brand values and target audience preferences.

            Consider these aspects for each campaign:
            - Cultural relevance and sensitivity
            - Cross-platform integration possibilities
            - Viral potential and shareability
            - Long-term brand building potential
            - Measurable business impact

            Format each campaign as a structured output with clear sections and detailed subsections."""
        )

    async def generate_campaign_ideas(self, company_analysis: Dict) -> List[Dict]:
        """
        Generate campaign ideas based on company analysis.
        
        Args:
            company_analysis (Dict): Analyzed company information
            
        Returns:
            List[Dict]: List of campaign ideas with details
        """
        
        print(company_analysis)
        
        
        # Extract information from company analysis
        company_info = company_analysis.get("company_summary", "")
        target_audience = company_analysis.get("target_audience", "")
        brand_values = company_analysis.get("brand_values", "")

        # Create chain for campaign generation
        chain = LLMChain(llm=self.llm, prompt=self.campaign_prompt)
        
        # Generate campaign ideas
        result = await chain.arun({
            "company_info": company_info,
            "target_audience": target_audience,
            "brand_values": brand_values,
            "num_campaigns": str(self.num_campaigns)
        })

        # Process and structure the response
        campaigns = self._process_campaign_response(result)
        
        # Add prompt suggestions for each campaign
        campaigns = self._add_prompt_suggestions(campaigns)

        return campaigns

    def _process_campaign_response(self, response: str) -> List[Dict]:
        """Process raw LLM response into structured campaign data."""
        # Split the response into individual campaigns
        campaigns = []
        current_campaign = {}
        current_section = None
        subsection_data = {}
        
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Start of a new campaign
            if line.startswith('Campaign'):
                if current_campaign:
                    if subsection_data:
                        current_campaign[current_section] = subsection_data
                    campaigns.append(current_campaign)
                current_campaign = {'campaign_name': line.split(':', 1)[1].strip() if ':' in line else line}
                current_section = None
                subsection_data = {}
            
            # Main section headers
            elif any(line.startswith(str(i)) for i in range(1, 10)):
                if current_section and subsection_data:
                    current_campaign[current_section] = subsection_data
                current_section = line.split(':', 1)[0].split('.')[1].strip().lower().replace(' ', '_')
                if ':' in line:
                    current_campaign[current_section] = line.split(':', 1)[1].strip()
                else:
                    subsection_data = {}
            
            # Subsection content
            elif line.startswith('-') and current_section:
                key = line.lstrip('- ').split(':', 1)[0].strip().lower().replace(' ', '_')
                value = line.split(':', 1)[1].strip() if ':' in line else line.lstrip('- ').strip()
                subsection_data[key] = value
            
            # Regular key-value pairs
            elif ':' in line and not line.startswith('-'):
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                current_campaign[key] = value

        # Add the last campaign
        if current_campaign:
            if subsection_data:
                current_campaign[current_section] = subsection_data
            campaigns.append(current_campaign)

        return campaigns[:self.num_campaigns]  # Ensure we only return requested number of campaigns

    def _add_prompt_suggestions(self, campaigns: List[Dict]) -> List[Dict]:
        """Add image prompt suggestions for each campaign."""
        for campaign in campaigns:
            print(campaign)
            visual_theme = campaign.get('visual_theme_description', {})
            if isinstance(visual_theme, dict):
                theme_desc = (
                    f"Color palette: {visual_theme.get('color_palette', 'professional')}. "
                    f"Style: {visual_theme.get('photography_illustration_style', 'modern')}. "
                    f"Elements: {visual_theme.get('key_visual_elements', 'clean and minimal')}. "
                    f"Mood: {visual_theme.get('mood_and_atmosphere', 'professional')}"
                )
            else:
                theme_desc = visual_theme

            emotional_appeal = campaign.get('key_emotional_appeal', {})
            if isinstance(emotional_appeal, dict):
                emotion_desc = (
                    f"{emotional_appeal.get('primary_emotion', 'professional')} mood with "
                    f"{emotional_appeal.get('supporting_psychological_triggers', 'trust and reliability')}"
                )
            else:
                emotion_desc = emotional_appeal

            # Create product-focused prompt suggestion
            product_prompt = (
                f"{theme_desc}. "
                f"Focus on {campaign.get('core_message', '')}. "
                f"Style: Professional photography, {emotion_desc}, "
                "photorealistic quality, advertisement composition, "
                "product-centric, commercial lighting"
            )

            # Create brand-focused prompt suggestion
            brand_prompt = (
                f"Scene capturing {emotion_desc} through "
                f"{theme_desc}. "
                f"Emphasizing: {campaign.get('core_message', '')}. "
                "Style: Cinematic lighting, emotional depth, photorealistic quality, "
                "lifestyle photography, brand storytelling"
            )

            # Create social media prompt suggestion
            social_focus = campaign.get('social_media_focus', {})
            if isinstance(social_focus, dict):
                platforms = social_focus.get('primary_platforms', '')
                content_format = social_focus.get('content_format_recommendations', '')
            else:
                platforms = social_focus
                content_format = 'engaging social media content'

            social_prompt = (
                f"Social media content for {platforms}. "
                f"{theme_desc}. "
                f"Format: {content_format}. "
                f"Style: {emotion_desc}, "
                "high engagement, platform-optimized, scroll-stopping visuals"
            )

            campaign['prompt_suggestions'] = {
                'product_focused': product_prompt.strip(),
                'brand_focused': brand_prompt.strip(),
                'social_media': social_prompt.strip()
            }

        return campaigns

# # Example usage
# if __name__ == "__main__":
#     import asyncio
#     import json
#     from ...config.settings import AzureSettings

#     async def test_campaign_generator():
#         # Initialize with Azure settings
#         azure_settings = AzureSettings(
#             deployment_name="your-deployment-name",
#             api_base="your-api-base",
#             api_key="your-api-key",
#             api_version="your-api-version"
#         )
#         generator = CampaignIdeaGenerator(azure_settings)
        
#         test_analysis = {
#             "company_summary": """
#             EcoTech Solutions is a sustainable technology company specializing in smart home devices.
#             They produce energy-efficient thermostats and power monitoring systems that help homeowners
#             reduce their carbon footprint while saving money. Their products feature sleek, modern design
#             and integrate with most smart home ecosystems.
#             """,
#             "target_audience": """
#             Environmentally conscious homeowners aged 25-45, tech-savvy professionals who value both
#             sustainability and modern design. They are willing to invest in quality products that help
#             reduce their environmental impact while maintaining a comfortable lifestyle.
#             """,
#             "brand_values": """
#             Innovation, Sustainability, User-Friendly Design, Environmental Responsibility, Quality
#             """
#         }
        
#         try:
#             campaigns = await generator.generate_campaign_ideas(test_analysis)
#             print(json.dumps(campaigns, indent=2))
#         except Exception as e:
#             print(f"Error in test: {str(e)}")

#     asyncio.run(test_campaign_generator())
