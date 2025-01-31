import random
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import render, get_object_or_404

from chit_chat.views import get_topics
from zappycode.settings import DISCOURSE_BASE_URL
from .models import Lecture, Section, Course
from sitewide.models import ZappyUser

import requests
from django.contrib import messages


@login_required
def download_video(request, lecture_id):
    lecture = get_object_or_404(Lecture, pk=lecture_id)
    user = ZappyUser.objects.get(email=request.user.email)
    if not lecture.download_url:
        lecture.get_download_url()

    # checking user permissions in case of open download url
    # outside of download button
    if user.active_membership:
        file_name = str(lecture.vimeo_video_id) + '.mp4'
        req = requests.get(lecture.download_url, stream=True, timeout=(5, 10))
        if req.status_code == 200:
            response = StreamingHttpResponse(req, content_type='video/mp4')
            response['Content-Disposition'] = 'attachment; filename=' + str(file_name)
            return response
        else:
            messages.warning(request, 'Bummer! Your download has failed')
            return render(request, 'courses/view_lecture.html', {'lecture': lecture})


def view_lecture(request, course_slug, lecturepk, lecture_slug):
    lecture = get_object_or_404(Lecture, pk=lecturepk)
    if not lecture.thumbnail_url:
        lecture.thumbnail_url = lecture.get_thumbnail_url()
        lecture.save()

    #  get issues from specific category to fill chit chat q&a box
    topics = get_topics(course_slug)
    return render(request, 'courses/view_lecture.html', {
        'lecture': lecture,
        'topics': topics[0],
        'table_title': topics[1],
        'discourse_url': DISCOURSE_BASE_URL[(DISCOURSE_BASE_URL.find('://') + 3):]
    })


def course_landing_page(request, course_slug):
    videos_number = 0
    course = get_object_or_404(Course, slug=course_slug)

    # count number of videos
    sections_ids = course.sections.values_list('id', flat=True)
    all_course_lectures = Lecture.objects.filter(section_id__in=sections_ids)
    for lecture in all_course_lectures:
        if lecture.vimeo_video_id:
            videos_number += 1

    # collect ids for choosing random courses (for right side snippets)
    ids = Course.objects.values_list('id', flat=True)
    records_number = 4
    # pull random ids
    rand_ids = random.sample(list(ids), records_number)
    # collect random records
    random_records = Course.objects.filter(id__in=rand_ids)

    # get most popular issues to fill chit chat box
    topics = get_topics('top')
    return render(request, 'courses/course_landing_page.html', {
        'rand_courses': random_records,
        'videos_number': videos_number,
        'course': course,
        'topics': topics[0],
        'table_title': topics[1],
        'discourse_url': DISCOURSE_BASE_URL[(DISCOURSE_BASE_URL.find('://') + 3):]
    })


def all_courses(request):
    courses = Course.objects.filter(published=True).order_by('-release_date')

    # get issues to fill chit chat box
    topics = get_topics('last')

    return render(request, 'courses/all_courses.html', {
        'courses': courses,
        'topics': topics[0],
        'table_title': topics[1],
        'discourse_url': DISCOURSE_BASE_URL[(DISCOURSE_BASE_URL.find('://') + 3):]
    })
