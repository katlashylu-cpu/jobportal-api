import factory
from django.contrib.auth import get_user_model

from jobs.models import Application, Company, Job, Skill

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user_{n}@example.com")
    role = User.ROLE_CANDIDATE

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop('password', 'StrongPass123!')
        user = super()._create(model_class, *args, **kwargs)
        user.set_password(password)
        user.save()
        return user


class RecruiterFactory(UserFactory):
    role = User.ROLE_RECRUITER


class CandidateFactory(UserFactory):
    role = User.ROLE_CANDIDATE


class AdminFactory(UserFactory):
    role = User.ROLE_ADMIN
    is_staff = True
    is_superuser = True


class CompanyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Company

    name = factory.Sequence(lambda n: f"Company {n}")
    description = "A tech company"
    website = "https://example.com"
    location = "Hyderabad"
    owner = factory.SubFactory(RecruiterFactory)


class SkillFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Skill

    name = factory.Sequence(lambda n: f"Skill_{n}")


class JobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Job
        skip_postgeneration_save = True

    company = factory.SubFactory(CompanyFactory)
    title = factory.Sequence(lambda n: f"Software Engineer {n}")
    description = "Exciting backend development opportunity."
    location = "Hyderabad"
    job_type = Job.JOB_TYPE_FULL_TIME
    salary_min = 500000
    salary_max = 1200000
    is_active = True

    @factory.post_generation
    def skills(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.skills.add(*extracted)


class ApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Application

    job = factory.SubFactory(JobFactory)
    candidate = factory.SubFactory(CandidateFactory)
    cover_letter = "I am excited to apply for this role."
    status = Application.STATUS_APPLIED
