from pydantic import BaseModel, Field
from typing import List, Dict

# GitHub Agent Output Models
class RepositoryReview(BaseModel):
    name: str = Field(description="Name of the repository")
    quality_score: int = Field(description="Code/Project quality score from 0 to 100")
    key_technologies: List[str] = Field(description="Key languages, libraries, and frameworks detected")
    review_comments: str = Field(description="Detailed evaluation comments on project architecture, code quality, and best practices")
    documentation_rating: str = Field(description="Documentation quality: Poor, Fair, Good, or Excellent")

class GitHubAnalysisOutput(BaseModel):
    portfolio_score: int = Field(description="Overall portfolio score from 0 to 100")
    strengths: List[str] = Field(description="Key strengths of the GitHub profile and codebases")
    weaknesses: List[str] = Field(description="Key areas of improvement or weaknesses found in the repositories")
    repository_reviews: List[RepositoryReview] = Field(description="Analysis details for each repository")
    primary_tech_stack: List[str] = Field(description="Core technologies identified across all repos")

# Resume Agent Output Models
class ProjectBullet(BaseModel):
    repo_name: str = Field(description="Name of the repository the bullet points are for")
    bullets: List[str] = Field(description="3-4 ATS-ready, action-oriented bullet points using the STAR method (Situation, Task, Action, Result)")

class ResumeImprovementsOutput(BaseModel):
    general_improvements: List[str] = Field(description="Actionable general tips to improve the resume format, layout, and content based on GitHub profile findings")
    ats_bullets: List[ProjectBullet] = Field(description="ATS-optimized bullet points mapping repositories to resume bullets")

# Career Agent Output Models
class RoadmapStep(BaseModel):
    step_number: int = Field(description="Order of this step in the learning timeline")
    topic: str = Field(description="What needs to be learned")
    skills_to_acquire: List[str] = Field(description="Specific technologies or concepts to study")
    recommended_resources: List[str] = Field(description="Suggested topics/keywords or resource names to study")
    estimated_time: str = Field(description="Estimated time to complete this step, e.g., '2 weeks'")

class RecommendedProject(BaseModel):
    title: str = Field(description="Title of the recommended project")
    description: str = Field(description="Description of what to build and why it fills a skill gap")
    suggested_tech_stack: List[str] = Field(description="Suggested technology stack for the project")
    difficulty: str = Field(description="Difficulty level: Beginner, Intermediate, or Advanced")

class RoleFit(BaseModel):
    role_name: str = Field(description="Name of the job role (e.g. Backend Engineer, Full Stack Engineer, AI/ML Engineer, Frontend Engineer, DevOps Engineer)")
    match_percentage: int = Field(description="Estimated match percentage from 0 to 100")
    reasoning: str = Field(description="Short explanation of why this role matches (or doesn't match) their current stack")

class CareerAnalysisOutput(BaseModel):
    skills_gap: List[str] = Field(description="Technologies or theoretical concepts missing from the candidate's current profile relative to industry expectations")
    roadmap: List[RoadmapStep] = Field(description="Sequential learning roadmap to close the skill gaps")
    recommended_projects: List[RecommendedProject] = Field(description="Suggested projects to build to gain missing skills and enhance the portfolio")
    role_fits: List[RoleFit] = Field(description="Suitability rating for various software engineering domains")

# Coordinator (Final Output) Model
class FinalPortfolioReviewReport(BaseModel):
    username: str = Field(description="GitHub username")
    name: str = Field(description="Name of the user, if available")
    bio: str = Field(description="Bio, if available")
    followers: int = Field(description="Follower count")
    avatar_url: str = Field(description="Profile avatar image URL")
    github_url: str = Field(description="GitHub profile URL")
    
    # Synthesized Sections
    github_analysis: GitHubAnalysisOutput
    resume_improvements: ResumeImprovementsOutput
    career_analysis: CareerAnalysisOutput
    
    summary: str = Field(description="A concise executive summary synthesizing all findings into an encouraging but constructive career roadmap guidance")
