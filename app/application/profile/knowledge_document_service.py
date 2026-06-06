import uuid
import json
from typing import List, Optional
from loguru import logger

from app.domain.profile.entities import (
    Profile, Resume, GitHubRepository, KnowledgeDocument
)
from app.domain.profile.repository_interfaces import IKnowledgeDocumentRepository

class KnowledgeDocumentService:
    """Service that converts domain entities into normalized KnowledgeDocument entities."""

    def __init__(self, knowledge_repo: IKnowledgeDocumentRepository):
        self.knowledge_repo = knowledge_repo

    async def generate_knowledge_documents(
        self,
        profile: Profile,
        resume: Optional[Resume],
        repositories: List[GitHubRepository]
    ) -> List[KnowledgeDocument]:
        """
        Normalizes and compiles all candidate data into KnowledgeDocuments.
        Clears previous knowledge documents for this profile and persists new ones.
        """
        logger.info(f"Generating normalized knowledge documents for profile: {profile.id}")
        
        # Clear out old knowledge documents
        await self.knowledge_repo.delete_by_profile_id(profile.id)
        
        normalized_docs: List[KnowledgeDocument] = []

        # 1. Base profile document
        profile_content = f"Candidate Profile Overview.\nGitHub URL: {profile.github_url}"
        profile_doc = KnowledgeDocument(
            profile_id=profile.id,
            source_type="profile",
            source_id=str(profile.id),
            title="Profile Summary - AI Shivam",
            content=profile_content,
            metadata={"github_url": profile.github_url}
        )
        normalized_docs.append(profile_doc)

        # 2. Resume document
        if resume and resume.extracted_text:
            resume_doc = KnowledgeDocument(
                profile_id=profile.id,
                source_type="resume",
                source_id=str(resume.id),
                title="Resume - AI Shivam",
                content=resume.extracted_text,
                metadata={
                    "cloudinary_url": resume.cloudinary_url,
                    "content_hash": resume.content_hash
                }
            )
            normalized_docs.append(resume_doc)

        # 3. GitHub repository documents
        for repo in repositories:
            # Format repository content for embeddings
            repo_text_content = (
                f"Repository Name: {repo.name}\n"
                f"Description: {repo.description or 'No description provided.'}\n"
                f"Topics/Tags: {', '.join(repo.topics) if repo.topics else 'None'}\n"
                f"Primary Programming Languages: {', '.join(repo.languages.keys()) if repo.languages else 'None'}\n"
                f"Default Branch: {repo.default_branch}\n"
                f"Last Pushed/Updated: {repo.last_updated.isoformat()}\n\n"
                f"README Content:\n{repo.readme_content or 'No README file available.'}"
            )
            
            repo_doc = KnowledgeDocument(
                profile_id=profile.id,
                source_type="repository",
                source_id=str(repo.id),
                title=f"GitHub Repository - {repo.name}",
                content=repo_text_content,
                metadata={
                    "repository_name": repo.name,
                    "topics": repo.topics,
                    "languages": list(repo.languages.keys()),
                    "last_updated": repo.last_updated.isoformat(),
                    "content_hash": repo.content_hash
                }
            )
            normalized_docs.append(repo_doc)

        # 4. Additional information document
        if profile.additional_information:
            add_info_doc = KnowledgeDocument(
                profile_id=profile.id,
                source_type="additional_information",
                source_id=str(profile.id),
                title="Additional Info - AI Shivam",
                content=profile.additional_information,
                metadata={}
            )
            normalized_docs.append(add_info_doc)

        # Save all generated documents
        for doc in normalized_docs:
            await self.knowledge_repo.save(doc)
            
        logger.info(f"Saved {len(normalized_docs)} knowledge documents for profile: {profile.id}")
        return normalized_docs
