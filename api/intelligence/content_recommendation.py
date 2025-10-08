"""
Intelligent Content Recommendation System for Carnatic Music Platform

Provides personalized exercise recommendations, raga suggestions,
and learning path optimization using collaborative filtering and
content-based recommendation algorithms.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
import math
from datetime import datetime, timedelta

class RecommendationType(Enum):
    EXERCISE = "exercise"
    RAGA = "raga"
    COMPOSITION = "composition"
    TECHNIQUE = "technique"
    CULTURAL_CONTENT = "cultural_content"

class DifficultyLevel(Enum):
    VERY_EASY = 1
    EASY = 2
    MODERATE = 3
    CHALLENGING = 4
    VERY_DIFFICULT = 5

@dataclass
class ContentItem:
    id: str
    title: str
    type: RecommendationType
    difficulty: DifficultyLevel
    tags: List[str]
    prerequisites: List[str]
    estimated_duration: int  # minutes
    cultural_significance: str
    learning_objectives: List[str]
    success_metrics: Dict[str, float]

@dataclass
class UserInteraction:
    user_id: int
    content_id: str
    interaction_type: str  # 'completed', 'attempted', 'skipped', 'bookmarked'
    rating: Optional[float]  # 1-5 scale
    time_spent: int  # minutes
    success_score: float  # 0-1 scale
    timestamp: datetime

@dataclass
class RecommendationResult:
    content_id: str
    score: float
    reasoning: str
    confidence: float
    estimated_success_probability: float
    prerequisites_met: bool
    personalization_factors: List[str]

class ContentRecommendationEngine:
    """
    Advanced recommendation system combining collaborative filtering,
    content-based filtering, and pedagogical sequencing for optimal
    personalized learning experiences in Carnatic music education.
    """

    def __init__(self):
        self.content_catalog: Dict[str, ContentItem] = {}
        self.user_interactions: Dict[int, List[UserInteraction]] = defaultdict(list)
        self.user_profiles: Dict[int, Dict[str, Any]] = {}
        self.content_similarities: Dict[Tuple[str, str], float] = {}
        self.user_similarities: Dict[Tuple[int, int], float] = {}

        # Initialize content catalog
        self._initialize_content_catalog()

        # Recommendation weights
        self.recommendation_weights = {
            'collaborative_filtering': 0.25,
            'content_based': 0.25,
            'pedagogical_sequence': 0.30,
            'user_preferences': 0.15,
            'cultural_progression': 0.05
        }

    def _initialize_content_catalog(self):
        """Initialize the content catalog with Carnatic music content"""

        # Sarali Varisai exercises
        sarali_exercises = [
            ContentItem(
                id="sarali_basic_arohanam",
                title="Basic Arohanam - Sa Ri Ga Ma Pa Da Ni Sa",
                type=RecommendationType.EXERCISE,
                difficulty=DifficultyLevel.VERY_EASY,
                tags=["sarali_varisai", "arohanam", "basic", "foundation"],
                prerequisites=[],
                estimated_duration=15,
                cultural_significance="The foundational ascending scale practice in Carnatic music",
                learning_objectives=["Master basic swara pronunciation", "Develop pitch accuracy"],
                success_metrics={"accuracy": 0.8, "consistency": 0.7}
            ),
            ContentItem(
                id="sarali_basic_avarohanam",
                title="Basic Avarohanam - Sa Ni Da Pa Ma Ga Ri Sa",
                type=RecommendationType.EXERCISE,
                difficulty=DifficultyLevel.VERY_EASY,
                tags=["sarali_varisai", "avarohanam", "basic", "foundation"],
                prerequisites=["sarali_basic_arohanam"],
                estimated_duration=15,
                cultural_significance="The foundational descending scale practice",
                learning_objectives=["Master descending swara patterns", "Develop melodic flow"],
                success_metrics={"accuracy": 0.8, "consistency": 0.7}
            ),
            ContentItem(
                id="sarali_combined_sequences",
                title="Combined Arohanam-Avarohanam Sequences",
                type=RecommendationType.EXERCISE,
                difficulty=DifficultyLevel.EASY,
                tags=["sarali_varisai", "combined", "intermediate"],
                prerequisites=["sarali_basic_arohanam", "sarali_basic_avarohanam"],
                estimated_duration=20,
                cultural_significance="Connecting ascending and descending patterns",
                learning_objectives=["Smooth transitions", "Continuous melodic flow"],
                success_metrics={"accuracy": 0.75, "consistency": 0.75, "flow": 0.8}
            )
        ]

        # Janta Varisai exercises
        janta_exercises = [
            ContentItem(
                id="janta_simple_doubles",
                title="Simple Janta Patterns - Sa Sa Ri Ri Ga Ga",
                type=RecommendationType.EXERCISE,
                difficulty=DifficultyLevel.EASY,
                tags=["janta_varisai", "doubles", "basic"],
                prerequisites=["sarali_combined_sequences"],
                estimated_duration=20,
                cultural_significance="Double note patterns for clarity and emphasis",
                learning_objectives=["Clear swara articulation", "Rhythmic precision"],
                success_metrics={"accuracy": 0.75, "rhythm": 0.8}
            ),
            ContentItem(
                id="janta_complex_transitions",
                title="Complex Janta Transition Patterns",
                type=RecommendationType.EXERCISE,
                difficulty=DifficultyLevel.MODERATE,
                tags=["janta_varisai", "transitions", "advanced"],
                prerequisites=["janta_simple_doubles"],
                estimated_duration=25,
                cultural_significance="Advanced patterns for melodic sophistication",
                learning_objectives=["Complex transitions", "Advanced technique"],
                success_metrics={"accuracy": 0.7, "complexity": 0.75}
            )
        ]

        # Raga-based content
        raga_content = [
            ContentItem(
                id="raga_mayamalavagowla_intro",
                title="Introduction to Raga Mayamalavagowla",
                type=RecommendationType.RAGA,
                difficulty=DifficultyLevel.EASY,
                tags=["raga", "mayamalavagowla", "melakarta", "morning"],
                prerequisites=["sarali_combined_sequences"],
                estimated_duration=30,
                cultural_significance="The 15th Melakarta raga, foundation of Carnatic music",
                learning_objectives=["Understand raga structure", "Basic improvisation"],
                success_metrics={"recognition": 0.8, "reproduction": 0.7}
            ),
            ContentItem(
                id="raga_mohanam_basics",
                title="Raga Mohanam - Pentatonic Beauty",
                type=RecommendationType.RAGA,
                difficulty=DifficultyLevel.EASY,
                tags=["raga", "mohanam", "janya", "pentatonic", "evening"],
                prerequisites=["raga_mayamalavagowla_intro"],
                estimated_duration=25,
                cultural_significance="Popular janya raga, gateway to improvisation",
                learning_objectives=["Pentatonic scales", "Simple improvisation"],
                success_metrics={"recognition": 0.8, "improvisation": 0.6}
            )
        ]

        # Cultural content
        cultural_content = [
            ContentItem(
                id="carnatic_history_origins",
                title="Origins and History of Carnatic Music",
                type=RecommendationType.CULTURAL_CONTENT,
                difficulty=DifficultyLevel.EASY,
                tags=["history", "culture", "theory", "background"],
                prerequisites=[],
                estimated_duration=20,
                cultural_significance="Understanding the rich heritage of Carnatic music",
                learning_objectives=["Historical context", "Cultural appreciation"],
                success_metrics={"comprehension": 0.8}
            ),
            ContentItem(
                id="tala_system_introduction",
                title="Understanding the Tala System",
                type=RecommendationType.TECHNIQUE,
                difficulty=DifficultyLevel.MODERATE,
                tags=["tala", "rhythm", "theory", "technique"],
                prerequisites=["janta_simple_doubles"],
                estimated_duration=35,
                cultural_significance="The rhythmic foundation of Carnatic music",
                learning_objectives=["Rhythm comprehension", "Beat keeping"],
                success_metrics={"rhythm_accuracy": 0.75, "beat_keeping": 0.8}
            )
        ]

        # Add all content to catalog
        all_content = sarali_exercises + janta_exercises + raga_content + cultural_content

        for content in all_content:
            self.content_catalog[content.id] = content

    def add_user_interaction(self, interaction: UserInteraction) -> None:
        """Record a user interaction with content"""
        self.user_interactions[interaction.user_id].append(interaction)

        # Update user profile
        self._update_user_profile(interaction.user_id, interaction)

    def _update_user_profile(self, user_id: int, interaction: UserInteraction) -> None:
        """Update user profile based on interaction"""

        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'preferred_content_types': defaultdict(float),
                'skill_progression': defaultdict(float),
                'engagement_patterns': defaultdict(float),
                'learning_pace': 1.0,
                'difficulty_preference': DifficultyLevel.EASY.value,
                'cultural_interest': 0.5
            }

        profile = self.user_profiles[user_id]
        content = self.content_catalog[interaction.content_id]

        # Update content type preferences
        profile['preferred_content_types'][content.type.value] += interaction.success_score

        # Update skill progression
        for tag in content.tags:
            profile['skill_progression'][tag] += interaction.success_score

        # Update engagement patterns
        engagement_factor = min(interaction.time_spent / content.estimated_duration, 2.0)
        profile['engagement_patterns'][content.type.value] += engagement_factor

        # Update learning pace
        expected_time = content.estimated_duration
        actual_time = interaction.time_spent
        if actual_time > 0:
            pace_factor = expected_time / actual_time
            profile['learning_pace'] = 0.8 * profile['learning_pace'] + 0.2 * pace_factor

        # Update difficulty preference
        if interaction.success_score >= 0.8:
            # User succeeded, might be ready for harder content
            target_difficulty = min(content.difficulty.value + 0.5, 5.0)
        elif interaction.success_score <= 0.5:
            # User struggled, prefer easier content
            target_difficulty = max(content.difficulty.value - 0.5, 1.0)
        else:
            # Maintain current level
            target_difficulty = content.difficulty.value

        profile['difficulty_preference'] = (0.7 * profile['difficulty_preference'] +
                                          0.3 * target_difficulty)

        # Update cultural interest
        if content.type == RecommendationType.CULTURAL_CONTENT:
            cultural_engagement = min(engagement_factor * interaction.success_score, 1.0)
            profile['cultural_interest'] = (0.8 * profile['cultural_interest'] +
                                          0.2 * cultural_engagement)

    def get_recommendations(
        self,
        user_id: int,
        num_recommendations: int = 5,
        content_types: Optional[List[RecommendationType]] = None
    ) -> List[RecommendationResult]:
        """Generate personalized content recommendations for a user"""

        if user_id not in self.user_profiles:
            # Cold start problem - use popularity-based recommendations
            return self._get_cold_start_recommendations(num_recommendations, content_types)

        # Get candidate content items
        candidates = self._get_candidate_content(user_id, content_types)

        # Calculate scores for each candidate
        recommendations = []

        for content_id, content in candidates.items():
            # Skip if prerequisites not met
            if not self._prerequisites_met(user_id, content):
                continue

            # Calculate recommendation score
            score, reasoning, factors = self._calculate_recommendation_score(user_id, content)

            # Calculate confidence and success probability
            confidence = self._calculate_confidence(user_id, content)
            success_prob = self._estimate_success_probability(user_id, content)

            recommendation = RecommendationResult(
                content_id=content_id,
                score=score,
                reasoning=reasoning,
                confidence=confidence,
                estimated_success_probability=success_prob,
                prerequisites_met=True,
                personalization_factors=factors
            )

            recommendations.append(recommendation)

        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x.score, reverse=True)

        return recommendations[:num_recommendations]

    def _get_candidate_content(
        self,
        user_id: int,
        content_types: Optional[List[RecommendationType]] = None
    ) -> Dict[str, ContentItem]:
        """Get candidate content items for recommendation"""

        candidates = {}
        user_interactions = {interaction.content_id for interaction in self.user_interactions[user_id]}

        for content_id, content in self.content_catalog.items():
            # Skip already completed content
            if content_id in user_interactions:
                # Check if user should retry or review
                if not self._should_recommend_retry(user_id, content_id):
                    continue

            # Filter by content type if specified
            if content_types and content.type not in content_types:
                continue

            candidates[content_id] = content

        return candidates

    def _should_recommend_retry(self, user_id: int, content_id: str) -> bool:
        """Determine if user should retry previously attempted content"""

        user_interactions_for_content = [
            interaction for interaction in self.user_interactions[user_id]
            if interaction.content_id == content_id
        ]

        if not user_interactions_for_content:
            return False

        # Get most recent interaction
        last_interaction = max(user_interactions_for_content, key=lambda x: x.timestamp)

        # Recommend retry if success score was low
        if last_interaction.success_score < 0.6:
            return True

        # Recommend review if it's been a while since last practice
        days_since_practice = (datetime.now() - last_interaction.timestamp).days
        if days_since_practice > 14:  # Two weeks
            return True

        return False

    def _prerequisites_met(self, user_id: int, content: ContentItem) -> bool:
        """Check if user has met all prerequisites for content"""

        if not content.prerequisites:
            return True

        completed_content = set()
        for interaction in self.user_interactions[user_id]:
            if interaction.success_score >= 0.7:  # Consider 70% as "completed"
                completed_content.add(interaction.content_id)

        return all(prereq in completed_content for prereq in content.prerequisites)

    def _calculate_recommendation_score(
        self,
        user_id: int,
        content: ContentItem
    ) -> Tuple[float, str, List[str]]:
        """Calculate comprehensive recommendation score"""

        profile = self.user_profiles[user_id]
        factors = []
        reasoning_parts = []

        # 1. Collaborative Filtering Score
        collab_score = self._calculate_collaborative_score(user_id, content.id)
        factors.append(f"collaborative_filtering: {collab_score:.3f}")

        # 2. Content-Based Score
        content_score = self._calculate_content_based_score(user_id, content)
        factors.append(f"content_based: {content_score:.3f}")

        # 3. Pedagogical Sequencing Score
        pedagogical_score = self._calculate_pedagogical_score(user_id, content)
        factors.append(f"pedagogical: {pedagogical_score:.3f}")

        # 4. User Preference Score
        preference_score = self._calculate_preference_score(user_id, content)
        factors.append(f"preferences: {preference_score:.3f}")

        # 5. Cultural Progression Score
        cultural_score = self._calculate_cultural_score(user_id, content)
        factors.append(f"cultural: {cultural_score:.3f}")

        # Combine scores using weights
        final_score = (
            self.recommendation_weights['collaborative_filtering'] * collab_score +
            self.recommendation_weights['content_based'] * content_score +
            self.recommendation_weights['pedagogical_sequence'] * pedagogical_score +
            self.recommendation_weights['user_preferences'] * preference_score +
            self.recommendation_weights['cultural_progression'] * cultural_score
        )

        # Generate reasoning
        if pedagogical_score > 0.8:
            reasoning_parts.append("optimal learning sequence placement")
        if preference_score > 0.8:
            reasoning_parts.append("matches your preferences")
        if content_score > 0.8:
            reasoning_parts.append("similar to content you've enjoyed")
        if collab_score > 0.7:
            reasoning_parts.append("popular with similar learners")

        if not reasoning_parts:
            reasoning_parts.append("general recommendation for your level")

        reasoning = f"Recommended because it provides {' and '.join(reasoning_parts)}."

        return final_score, reasoning, factors

    def _calculate_collaborative_score(self, user_id: int, content_id: str) -> float:
        """Calculate collaborative filtering score"""

        # Find similar users
        similar_users = self._find_similar_users(user_id, top_k=10)

        if not similar_users:
            return 0.5  # Neutral score for new users

        # Calculate weighted average rating
        weighted_sum = 0.0
        weight_sum = 0.0

        for similar_user_id, similarity in similar_users:
            # Find rating for this content by similar user
            user_rating = self._get_user_rating(similar_user_id, content_id)

            if user_rating is not None:
                weighted_sum += similarity * user_rating
                weight_sum += similarity

        if weight_sum == 0:
            return 0.5  # No similar user has rated this content

        return weighted_sum / weight_sum

    def _calculate_content_based_score(self, user_id: int, content: ContentItem) -> float:
        """Calculate content-based filtering score"""

        profile = self.user_profiles[user_id]

        # Calculate similarity to user's historical preferences
        content_score = 0.0

        # Content type preference
        type_preference = profile['preferred_content_types'].get(content.type.value, 0)
        content_score += 0.3 * min(type_preference / 5.0, 1.0)  # Normalize to 0-1

        # Tag-based similarity
        tag_score = 0.0
        for tag in content.tags:
            skill_level = profile['skill_progression'].get(tag, 0)
            tag_score += min(skill_level / 3.0, 1.0)  # Normalize

        if content.tags:
            content_score += 0.4 * (tag_score / len(content.tags))

        # Difficulty matching
        preferred_difficulty = profile['difficulty_preference']
        difficulty_diff = abs(content.difficulty.value - preferred_difficulty)
        difficulty_score = max(0, 1.0 - difficulty_diff / 4.0)  # Normalize to 0-1
        content_score += 0.3 * difficulty_score

        return min(content_score, 1.0)

    def _calculate_pedagogical_score(self, user_id: int, content: ContentItem) -> float:
        """Calculate pedagogical sequencing score"""

        # Check if this is the natural next step in learning progression
        profile = self.user_profiles[user_id]

        # Calculate readiness based on prerequisites
        prerequisite_strength = 0.0
        if content.prerequisites:
            for prereq in content.prerequisites:
                prereq_content = self.content_catalog.get(prereq)
                if prereq_content:
                    # Check user's mastery of prerequisite
                    mastery = self._get_content_mastery(user_id, prereq)
                    prerequisite_strength += mastery

            prerequisite_strength /= len(content.prerequisites)
        else:
            prerequisite_strength = 1.0  # No prerequisites

        # Calculate learning path coherence
        coherence_score = 0.0
        recent_content = self._get_recent_content_tags(user_id, days=7)

        # Bonus for content that builds on recent practice
        common_tags = set(content.tags) & set(recent_content)
        if common_tags:
            coherence_score = len(common_tags) / max(len(content.tags), 1)

        # Combine factors
        pedagogical_score = 0.7 * prerequisite_strength + 0.3 * coherence_score

        return min(pedagogical_score, 1.0)

    def _calculate_preference_score(self, user_id: int, content: ContentItem) -> float:
        """Calculate user preference alignment score"""

        profile = self.user_profiles[user_id]

        # Learning pace matching
        estimated_time = content.estimated_duration
        user_pace = profile['learning_pace']

        # Adjust expected time based on user's pace
        adjusted_time = estimated_time / user_pace

        # Prefer content that fits user's typical session length
        recent_durations = [
            interaction.time_spent for interaction in self.user_interactions[user_id][-10:]
            if interaction.time_spent > 0
        ]

        if recent_durations:
            avg_session_time = np.mean(recent_durations)
            time_match = 1.0 - abs(adjusted_time - avg_session_time) / max(adjusted_time, avg_session_time)
            time_score = max(0, time_match)
        else:
            time_score = 0.5  # Neutral for new users

        # Engagement pattern matching
        engagement_score = profile['engagement_patterns'].get(content.type.value, 0)
        normalized_engagement = min(engagement_score / 5.0, 1.0)

        # Combine preference factors
        preference_score = 0.6 * normalized_engagement + 0.4 * time_score

        return preference_score

    def _calculate_cultural_score(self, user_id: int, content: ContentItem) -> float:
        """Calculate cultural progression score"""

        profile = self.user_profiles[user_id]
        cultural_interest = profile['cultural_interest']

        if content.type == RecommendationType.CULTURAL_CONTENT:
            # Boost cultural content for culturally interested users
            return cultural_interest
        else:
            # Slightly prefer content with cultural significance for all users
            cultural_significance_length = len(content.cultural_significance)
            significance_score = min(cultural_significance_length / 100, 1.0)

            return 0.3 * cultural_interest + 0.7 * significance_score

    def _find_similar_users(self, user_id: int, top_k: int = 10) -> List[Tuple[int, float]]:
        """Find users similar to the given user"""

        if user_id not in self.user_profiles:
            return []

        target_profile = self.user_profiles[user_id]
        similarities = []

        for other_user_id, other_profile in self.user_profiles.items():
            if other_user_id == user_id:
                continue

            similarity = self._calculate_user_similarity(target_profile, other_profile)
            similarities.append((other_user_id, similarity))

        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def _calculate_user_similarity(self, profile1: Dict[str, Any], profile2: Dict[str, Any]) -> float:
        """Calculate similarity between two user profiles"""

        # Calculate cosine similarity for content preferences
        pref1 = profile1['preferred_content_types']
        pref2 = profile2['preferred_content_types']

        all_types = set(pref1.keys()) | set(pref2.keys())
        if not all_types:
            return 0.0

        vec1 = np.array([pref1.get(t, 0) for t in all_types])
        vec2 = np.array([pref2.get(t, 0) for t in all_types])

        # Cosine similarity
        if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
            content_sim = 0.0
        else:
            content_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

        # Difficulty preference similarity
        diff_pref_sim = 1.0 - abs(profile1['difficulty_preference'] - profile2['difficulty_preference']) / 4.0

        # Learning pace similarity
        pace_sim = 1.0 - abs(profile1['learning_pace'] - profile2['learning_pace']) / max(profile1['learning_pace'], profile2['learning_pace'])

        # Cultural interest similarity
        cultural_sim = 1.0 - abs(profile1['cultural_interest'] - profile2['cultural_interest'])

        # Weighted combination
        similarity = (0.4 * content_sim + 0.25 * diff_pref_sim +
                     0.2 * pace_sim + 0.15 * cultural_sim)

        return max(0.0, similarity)

    def _get_user_rating(self, user_id: int, content_id: str) -> Optional[float]:
        """Get user's rating for specific content"""

        interactions = [
            interaction for interaction in self.user_interactions[user_id]
            if interaction.content_id == content_id
        ]

        if not interactions:
            return None

        # Use most recent interaction's success score as implicit rating
        latest = max(interactions, key=lambda x: x.timestamp)

        # Convert success score (0-1) to rating (1-5)
        rating = 1 + latest.success_score * 4

        return rating

    def _get_content_mastery(self, user_id: int, content_id: str) -> float:
        """Get user's mastery level for specific content"""

        interactions = [
            interaction for interaction in self.user_interactions[user_id]
            if interaction.content_id == content_id
        ]

        if not interactions:
            return 0.0

        # Calculate mastery from interactions
        scores = [interaction.success_score for interaction in interactions]
        return max(scores)  # Best performance

    def _get_recent_content_tags(self, user_id: int, days: int = 7) -> List[str]:
        """Get tags from recently practiced content"""

        cutoff_date = datetime.now() - timedelta(days=days)
        recent_tags = []

        for interaction in self.user_interactions[user_id]:
            if interaction.timestamp >= cutoff_date:
                content = self.content_catalog.get(interaction.content_id)
                if content:
                    recent_tags.extend(content.tags)

        return recent_tags

    def _calculate_confidence(self, user_id: int, content: ContentItem) -> float:
        """Calculate confidence in the recommendation"""

        profile = self.user_profiles[user_id]

        # Base confidence on amount of user data
        num_interactions = len(self.user_interactions[user_id])
        data_confidence = min(num_interactions / 20.0, 1.0)  # Max confidence at 20 interactions

        # Confidence in difficulty match
        preferred_difficulty = profile['difficulty_preference']
        difficulty_confidence = 1.0 - abs(content.difficulty.value - preferred_difficulty) / 4.0

        # Prerequisites confidence
        prereq_confidence = 1.0 if self._prerequisites_met(user_id, content) else 0.3

        # Combined confidence
        confidence = 0.5 * data_confidence + 0.3 * difficulty_confidence + 0.2 * prereq_confidence

        return max(0.1, min(1.0, confidence))

    def _estimate_success_probability(self, user_id: int, content: ContentItem) -> float:
        """Estimate probability of user success with this content"""

        profile = self.user_profiles[user_id]

        # Base success rate from user's historical performance
        if self.user_interactions[user_id]:
            avg_success = np.mean([i.success_score for i in self.user_interactions[user_id]])
        else:
            avg_success = 0.6  # Default assumption

        # Adjust for difficulty match
        preferred_difficulty = profile['difficulty_preference']
        difficulty_factor = 1.0 - abs(content.difficulty.value - preferred_difficulty) / 8.0

        # Adjust for prerequisite mastery
        prereq_factor = 1.0
        if content.prerequisites:
            prereq_masteries = [self._get_content_mastery(user_id, prereq) for prereq in content.prerequisites]
            prereq_factor = np.mean(prereq_masteries) if prereq_masteries else 0.5

        # Adjust for content type preference
        type_preference = profile['preferred_content_types'].get(content.type.value, 0)
        type_factor = min(type_preference / 3.0, 1.0)

        # Combined probability
        success_prob = avg_success * (0.4 * difficulty_factor + 0.3 * prereq_factor + 0.3 * type_factor)

        return max(0.1, min(0.95, success_prob))

    def _get_cold_start_recommendations(
        self,
        num_recommendations: int = 5,
        content_types: Optional[List[RecommendationType]] = None
    ) -> List[RecommendationResult]:
        """Provide recommendations for new users (cold start problem)"""

        # Start with foundational content
        foundation_content_ids = [
            "sarali_basic_arohanam",
            "sarali_basic_avarohanam",
            "carnatic_history_origins",
            "sarali_combined_sequences",
            "raga_mayamalavagowla_intro"
        ]

        recommendations = []

        for content_id in foundation_content_ids[:num_recommendations]:
            if content_id not in self.content_catalog:
                continue

            content = self.content_catalog[content_id]

            # Skip if content type filtering is active
            if content_types and content.type not in content_types:
                continue

            recommendation = RecommendationResult(
                content_id=content_id,
                score=0.8,  # High score for foundational content
                reasoning="Essential foundational content for new Carnatic music learners.",
                confidence=0.9,
                estimated_success_probability=0.8,
                prerequisites_met=True,
                personalization_factors=["cold_start", "foundational"]
            )

            recommendations.append(recommendation)

        return recommendations[:num_recommendations]

    def get_learning_path(
        self,
        user_id: int,
        goal_content_id: str,
        max_steps: int = 10
    ) -> Optional[List[str]]:
        """Generate a learning path to reach a specific content goal"""

        if goal_content_id not in self.content_catalog:
            return None

        goal_content = self.content_catalog[goal_content_id]

        # Check if goal is already achievable
        if self._prerequisites_met(user_id, goal_content):
            return [goal_content_id]

        # Build prerequisite graph and find shortest path
        path = self._find_learning_path(user_id, goal_content_id, max_steps)

        return path

    def _find_learning_path(
        self,
        user_id: int,
        goal_content_id: str,
        max_steps: int,
        visited: Optional[Set[str]] = None
    ) -> Optional[List[str]]:
        """Find learning path using recursive approach"""

        if visited is None:
            visited = set()

        if goal_content_id in visited:
            return None  # Circular dependency

        visited.add(goal_content_id)

        goal_content = self.content_catalog[goal_content_id]

        # If prerequisites are met, return direct path
        if self._prerequisites_met(user_id, goal_content):
            return [goal_content_id]

        if max_steps <= 1:
            return None  # Max depth reached

        # Find paths through prerequisites
        for prereq_id in goal_content.prerequisites:
            if prereq_id not in self.content_catalog:
                continue

            # Recursively find path to prerequisite
            prereq_path = self._find_learning_path(
                user_id, prereq_id, max_steps - 1, visited.copy()
            )

            if prereq_path:
                # Check if all other prerequisites would be met
                other_prereqs = [p for p in goal_content.prerequisites if p != prereq_id]
                if all(self._prerequisites_met(user_id, self.content_catalog[p]) for p in other_prereqs):
                    return prereq_path + [goal_content_id]

        return None  # No valid path found

    def get_user_analytics(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive analytics for a user"""

        if user_id not in self.user_profiles:
            return None

        profile = self.user_profiles[user_id]
        interactions = self.user_interactions[user_id]

        # Calculate completion rates by content type
        completion_rates = defaultdict(lambda: {'attempted': 0, 'completed': 0})

        for interaction in interactions:
            content = self.content_catalog.get(interaction.content_id)
            if content:
                content_type = content.type.value
                completion_rates[content_type]['attempted'] += 1
                if interaction.success_score >= 0.7:
                    completion_rates[content_type]['completed'] += 1

        # Calculate rates
        for type_data in completion_rates.values():
            if type_data['attempted'] > 0:
                type_data['rate'] = type_data['completed'] / type_data['attempted']
            else:
                type_data['rate'] = 0.0

        # Learning progression analysis
        progression = {}
        for tag, skill_level in profile['skill_progression'].items():
            progression[tag] = {
                'current_level': skill_level,
                'proficiency': min(skill_level / 5.0, 1.0)  # Normalize to 0-1
            }

        analytics = {
            'user_id': user_id,
            'profile_summary': {
                'learning_pace': profile['learning_pace'],
                'preferred_difficulty': profile['difficulty_preference'],
                'cultural_interest': profile['cultural_interest']
            },
            'completion_rates': dict(completion_rates),
            'skill_progression': progression,
            'total_interactions': len(interactions),
            'average_success_score': np.mean([i.success_score for i in interactions]) if interactions else 0,
            'preferred_content_types': dict(profile['preferred_content_types']),
            'recent_activity': len([i for i in interactions if (datetime.now() - i.timestamp).days <= 7])
        }

        return analytics