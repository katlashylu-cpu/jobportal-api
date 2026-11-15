from django.contrib import admin

from .models import Application, Company, Job, Skill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'location', 'created_at')
    search_fields = ('name', 'location', 'owner__username')
    list_filter = ('created_at',)
    raw_id_fields = ('owner',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'company', 'location', 'job_type', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'location', 'company__name')
    list_filter = ('is_active', 'job_type', 'created_at')
    filter_horizontal = ('skills',)
    raw_id_fields = ('company',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'candidate', 'status', 'applied_at')
    search_fields = ('job__title', 'candidate__username', 'candidate__email')
    list_filter = ('status', 'applied_at')
    raw_id_fields = ('job', 'candidate')
