from rest_framework import serializers

from .models import Application, Company, Job, Skill


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name')


class CompanySerializer(serializers.ModelSerializer):
    owner_id = serializers.ReadOnlyField(source='owner.id')
    owner_username = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Company
        fields = (
            'id',
            'name',
            'description',
            'website',
            'location',
            'owner_id',
            'owner_username',
            'created_at',
        )
        read_only_fields = ('id', 'created_at', 'owner_id', 'owner_username')

    def validate(self, attrs):
        request = self.context.get('request')
        # Only check on creation
        if not self.instance and request and request.user.is_authenticated:
            if Company.objects.filter(owner=request.user).exists():
                raise serializers.ValidationError(
                    {"name": ["You already have a registered company profile. Recruiters may only create one company."]}
                )
        return attrs


class JobSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Skill.objects.all(),
        source='skills',
        write_only=True,
        required=False,
    )

    class Meta:
        model = Job
        fields = (
            'id',
            'company',
            'title',
            'description',
            'location',
            'job_type',
            'salary_min',
            'salary_max',
            'skills',
            'skill_ids',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'company', 'created_at', 'updated_at')

    def validate(self, attrs):
        salary_min = attrs.get('salary_min', getattr(self.instance, 'salary_min', None))
        salary_max = attrs.get('salary_max', getattr(self.instance, 'salary_max', None))

        if salary_min is not None and salary_max is not None:
            if salary_min > salary_max:
                raise serializers.ValidationError(
                    {"salary_min": ["Must be less than or equal to salary_max."]}
                )
        return attrs


class ApplicationSerializer(serializers.ModelSerializer):
    job_id = serializers.ReadOnlyField(source='job.id')
    job_title = serializers.ReadOnlyField(source='job.title')
    company_name = serializers.ReadOnlyField(source='job.company.name')
    candidate_id = serializers.ReadOnlyField(source='candidate.id')
    candidate_username = serializers.ReadOnlyField(source='candidate.username')
    candidate_email = serializers.ReadOnlyField(source='candidate.email')

    class Meta:
        model = Application
        fields = (
            'id',
            'job_id',
            'job_title',
            'company_name',
            'candidate_id',
            'candidate_username',
            'candidate_email',
            'resume',
            'cover_letter',
            'status',
            'applied_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'job_id',
            'job_title',
            'company_name',
            'candidate_id',
            'candidate_username',
            'candidate_email',
            'status',
            'applied_at',
            'updated_at',
        )


class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ('resume', 'cover_letter')


class ApplicationStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Application.STATUS_CHOICES)
