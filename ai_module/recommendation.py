import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


# ── Human-readable time helper ─────────────────────────────────────────────
PRIORITY_LABELS = {
    'overdue': {'label': 'High Priority', 'badge': 'danger',   'icon': '🔴'},
    'upcoming': {'label': 'Medium Priority', 'badge': 'warning', 'icon': '🟡'},
    'future':   {'label': 'Low Priority',    'badge': 'info',    'icon': '🔵'},
}


def _days_human(days: int) -> str:
    """Convert a day count to a human-readable string (e.g. 365 → '1 year')."""
    days = abs(days)
    if days >= 365:
        years = days // 365
        return f"{years} year{'s' if years != 1 else ''}"
    if days >= 30:
        months = days // 30
        return f"{months} month{'s' if months != 1 else ''}"
    return f"{days} day{'s' if days != 1 else ''}"


class MissedDosePredictor:
    """
    ML-based missed dose prediction using RandomForest classifier.
    Predicts High Risk / Low Risk of missing upcoming vaccines.
    Approximate model accuracy ~85% on synthetic training data.
    """

    MODEL_ACCURACY = None   # set after training

    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=150,
            max_depth=6,
            random_state=42,
            class_weight='balanced'
        )
        self.le = LabelEncoder()
        self.is_trained = False
        self._train_on_synthetic_data()

    # ── Synthetic data generation ──────────────────────────────────────────
    def _generate_synthetic_data(self, n_samples=1500):
        """Generate realistic synthetic training data."""
        np.random.seed(42)
        data = []
        for _ in range(n_samples):
            age_months = np.random.randint(0, 240)
            completed = np.random.randint(0, 20)
            total = completed + np.random.randint(0, 10)
            pending = total - completed
            completion_rate = completed / max(total, 1)
            days_since_last = np.random.randint(0, 365)
            # Actual missed vaccines = overdue (pending where age > recommended)
            num_missed = np.random.randint(0, min(pending + 1, 8))
            has_child_profile = np.random.randint(0, 2)
            # How many dose series started but not finished
            incomplete_series = np.random.randint(0, 4)

            risk_score = (
                0.30 * (1 - completion_rate) +
                0.25 * min(num_missed / 5, 1) +
                0.20 * min(days_since_last / 365, 1) +
                0.10 * min(pending / 10, 1) +
                0.10 * min(incomplete_series / 4, 1) +
                0.05 * (1 - has_child_profile)
            )
            risk = 'High Risk' if risk_score > 0.42 else 'Low Risk'

            data.append({
                'age_months': age_months,
                'completed_vaccines': completed,
                'pending_vaccines': pending,
                'completion_rate': completion_rate,
                'days_since_last_vaccine': days_since_last,
                'num_missed_before': num_missed,
                'has_child_profile': has_child_profile,
                'incomplete_series': incomplete_series,
                'risk': risk
            })
        return pd.DataFrame(data)

    def _train_on_synthetic_data(self):
        df = self._generate_synthetic_data()
        feature_cols = [
            'age_months', 'completed_vaccines', 'pending_vaccines',
            'completion_rate', 'days_since_last_vaccine',
            'num_missed_before', 'has_child_profile', 'incomplete_series'
        ]
        X = df[feature_cols]
        y = self.le.fit_transform(df['risk'])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        self.model.fit(X_train, y_train)
        self.is_trained = True

        # Calculate and store approximate model accuracy
        y_pred = self.model.predict(X_test)
        MissedDosePredictor.MODEL_ACCURACY = round(
            accuracy_score(y_test, y_pred) * 100, 1
        )

    # ── Prediction ─────────────────────────────────────────────────────────
    def predict(self, user_data: dict) -> dict:
        """
        Predict missed dose risk for a user.

        user_data keys:
            - age_months: int
            - completed_vaccines: int
            - pending_vaccines: int
            - days_since_last_vaccine: int
            - num_missed_before: int   (actual missed/overdue vaccines count)
            - has_child_profile: int (0 or 1)
            - incomplete_series: int (optional)
        """
        completed = user_data.get('completed_vaccines', 0)
        pending = user_data.get('pending_vaccines', 0)
        total = completed + pending
        completion_rate = completed / max(total, 1)

        features = np.array([[
            user_data.get('age_months', 0),
            completed,
            pending,
            completion_rate,
            user_data.get('days_since_last_vaccine', 0),
            user_data.get('num_missed_before', 0),
            user_data.get('has_child_profile', 0),
            user_data.get('incomplete_series', 0),
        ]])

        pred = self.model.predict(features)[0]
        proba = self.model.predict_proba(features)[0]
        risk_label = self.le.inverse_transform([pred])[0]
        confidence = float(max(proba))
        risk_score = round(confidence * 100, 1)

        # Map confidence → human-readable level
        if confidence >= 0.80:
            confidence_label = 'High Confidence'
        elif confidence >= 0.60:
            confidence_label = 'Medium Confidence'
        else:
            confidence_label = 'Low Confidence'

        return {
            'risk_level': risk_label,
            'risk_score': risk_score,
            'confidence': round(confidence * 100, 1),
            'confidence_label': confidence_label,
            'is_high_risk': risk_label == 'High Risk',
            'completion_rate': round(completion_rate * 100, 1),
            'missed_count': user_data.get('num_missed_before', 0),
            'model_accuracy': MissedDosePredictor.MODEL_ACCURACY,
            'recommendations': self._get_recommendations(risk_label, user_data, completion_rate)
        }

    def _get_recommendations(self, risk_level: str, user_data: dict,
                             completion_rate: float) -> list:
        recs = []
        missed = user_data.get('num_missed_before', 0)
        days_since = user_data.get('days_since_last_vaccine', 0)
        pending = user_data.get('pending_vaccines', 0)

        if risk_level == 'High Risk':
            recs.append('⚠️ Schedule a vaccination appointment as soon as possible.')
            recs.append('📱 Enable vaccine reminders on your SmartVax dashboard.')
            if missed > 0:
                recs.append(
                    f'📋 You have {missed} overdue vaccine(s) — contact your healthcare provider.'
                )
            if pending > 5:
                recs.append('📋 Multiple pending vaccines detected — create a catch-up plan.')
        else:
            recs.append('✅ You are on track with your vaccination schedule.')
            recs.append('📅 Keep monitoring upcoming vaccines in your schedule.')

        if days_since > 180:
            recs.append('🕐 It has been over 6 months since your last vaccine — check your schedule.')

        if completion_rate < 0.50:
            recs.append('📊 Your completion rate is below 50%. Aim to complete overdue vaccines first.')

        return recs


class VaccineRecommendationEngine:
    """
    Age-based + history-based vaccine recommendation engine
    with priority levels (High / Medium / Low).
    """

    # Months difference thresholds
    OVERDUE_THRESHOLD = 0      # months_diff <= 0   → overdue (High priority)
    UPCOMING_THRESHOLD = 3     # months_diff <= 3   → upcoming (Medium priority)
    FUTURE_THRESHOLD = 24      # months_diff <= 24  → future (Low priority)

    def get_recommendations(self, user_age_months: int,
                            completed_vaccine_ids: list,
                            all_vaccines: list) -> dict:
        """
        Returns categorized vaccine recommendations with priority metadata.
        """
        due_now = []       # Overdue — HIGH priority
        upcoming = []      # Due within 3 months — MEDIUM priority
        future = []        # Due in 3-24 months — LOW priority
        completed = []     # Already taken

        for v in all_vaccines:
            if v.id in completed_vaccine_ids:
                completed.append(v)
                continue

            months_diff = v.recommended_age_months - user_age_months

            if months_diff <= self.OVERDUE_THRESHOLD:
                days_overdue = abs(int(months_diff * 30.44))
                due_now.append({
                    'vaccine': v,
                    'months_diff': months_diff,
                    'priority': 'High',
                    'priority_badge': 'danger',
                    'label': '🔴 Due Now',
                    'days_overdue': days_overdue,
                    'days_overdue_display': _days_human(days_overdue),
                })
            elif months_diff <= self.UPCOMING_THRESHOLD:
                days_until = int(months_diff * 30.44)
                upcoming.append({
                    'vaccine': v,
                    'months_diff': months_diff,
                    'priority': 'Medium',
                    'priority_badge': 'warning',
                    'label': '🟡 Upcoming',
                    'days_until': days_until,
                    'days_until_display': _days_human(days_until),
                })
            elif months_diff <= self.FUTURE_THRESHOLD:
                days_until = int(months_diff * 30.44)
                future.append({
                    'vaccine': v,
                    'months_diff': months_diff,
                    'priority': 'Low',
                    'priority_badge': 'info',
                    'label': '🔵 Scheduled',
                    'days_until': days_until,
                    'days_until_display': _days_human(days_until),
                })

        # Sort by priority (most urgent first)
        due_now.sort(key=lambda x: x['months_diff'])
        upcoming.sort(key=lambda x: x['months_diff'])
        future.sort(key=lambda x: x['months_diff'])

        # Next vaccine due
        next_vaccine = None
        if upcoming:
            next_vaccine = upcoming[0]
        elif due_now:
            next_vaccine = due_now[0]

        # For template backward compat — expose plain vaccine objects too
        due_now_vaccines = [item['vaccine'] for item in due_now]
        upcoming_vaccines = [item['vaccine'] for item in upcoming]

        return {
            # Rich objects with priority
            'due_now_detailed': due_now,
            'upcoming_detailed': upcoming,
            'future_detailed': future,
            # Plain vaccine objects (backward compat)
            'due_now': due_now_vaccines,
            'upcoming': upcoming_vaccines,
            'future': [item['vaccine'] for item in future],
            'completed': completed,
            # Counts
            'total': len(all_vaccines),
            'completed_count': len(completed),
            'pending_count': len(due_now),
            'upcoming_count': len(upcoming),
            'completion_percentage': round(
                len(completed) / max(len(all_vaccines), 1) * 100, 1
            ),
            # Next vaccine
            'next_vaccine': next_vaccine,
        }

    def get_age_appropriate_vaccines(self, user_age_months: int,
                                     all_vaccines: list) -> list:
        return [v for v in all_vaccines
                if v.recommended_age_months <= user_age_months + 3]


# ── Singleton instances ─────────────────────────────────────────────────────
predictor = MissedDosePredictor()
recommender = VaccineRecommendationEngine()
