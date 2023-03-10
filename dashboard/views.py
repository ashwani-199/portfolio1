from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template.defaultfilters import slugify
from me.models import Message
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .decorators import admin_only
from .forms import MyProjectForm, ProjectImageForm
from .models import GuestLocation, MyProject, ProjectImage, ProjectTool
from .serializer import GuestLocationSerializer


@login_required(login_url='login')
def dashboard(request):
    visitors = GuestLocation.objects.all()
    messages = Message.objects.all()
    projects = MyProject.objects.all()

    context = {'messages': messages, 'visitors': visitors, 'projects': projects, 'project1': projects.count() }
    return render(request, 'dashboard/dashboard.html', context)


@login_required(login_url='login')
def manage_projects(request):
    projects = MyProject.objects.all()

    context = {'projects': projects}
    return render(request, 'dashboard/manage-projects.html', context)


@login_required(login_url='login')
@admin_only
def add_project(request):
    form = MyProjectForm()

    if request.method == 'POST':
        '''
        check if the request coming from tools form
        '''
        if request.POST.get('tools'):
            ProjectTool.objects.create(
                tool=request.POST.get('tools')
            )
        else:
            form = MyProjectForm(request.POST)
            if form.is_valid():
                data = form.save(commit=False)
                data.slug = slugify(form.cleaned_data['title'])
                data.save()
                '''
                add project images
                '''
                images = request.FILES.getlist('images')
                print(images)
                for image in images:
                    ProjectImage.objects.create(
                    product=data,
                    image=image,
                    order=images.index(image),
                )

            return redirect('man_pro')

    context = {'form': form}
    return render(request, 'dashboard/add-project.html', context)


@login_required(login_url='login')
@admin_only
def update_project(request, slug):
    project = MyProject.objects.get(slug=slug)
    form = MyProjectForm(instance=project)
    if request.method == 'POST':
        form = MyProjectForm(request.POST, instance=project)
        if form.is_valid():
            data = form.save()
            '''
            add project images
            '''
            images = request.FILES.getlist('images')
            print(images)
            if images:
                ProjectImage.objects.filter(product=data).delete()
                for image in images:
                    ProjectImage.objects.create(
                        product=data,
                        image=image,
                        order=images.index(image),
                    )

            return redirect('man_pro')

    context = {'form': form, 'project': project}
    return render(request, 'dashboard/update-project.html', context)


@login_required(login_url='login')
@admin_only
def delete_project(request, pk):
    try:
        project = MyProject.objects.get(id=pk)
        project.delete()
        return redirect('man_pro')
    except ObjectDoesNotExist:
        return HttpResponse('Page not found (404)')


def login_user(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        try:
            User.objects.get(username=username)
        except:
            messages.error(request, 'User dose not exist')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'User name or password is incorrect')

    return render(request, 'dashboard/login.html')


def logout_user(request):
    logout(request)
    return redirect('login')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_view(request):
    product = GuestLocation.objects.all()
    serializer = GuestLocationSerializer(product, many=True)

    return Response(serializer.data)
