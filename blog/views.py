import glob, re, os
from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail, EmailMessage
from django.shortcuts import get_object_or_404, redirect
from django.template import RequestContext, loader, Context, Template
from django.utils import simplejson
from django.utils.html import strip_tags
from django.utils.encoding import smart_unicode
from blog.models import *

def base_view_data(template_name, data, request):
	if data is None:
		data = {}
	data['request'] = request
	data['template_name'] = template_name
	data['settings'] = settings
	data['pages'] = Page.objects.all().filter(type='published').order_by('-published')
	return data

def respond(template, data, request, mime=None):
	data = base_view_data(template, data, request)
	if mime is None:
		mime = 'text/html'
	t = loader.get_template(template)
	c = RequestContext(request, data)
	return HttpResponse(t.render(c), content_type=mime + "; charset=utf-8")

def page(request, page_slug):
	if request.user.is_authenticated():
		page = get_object_or_404(Page, slug=page_slug)
	else:
		page = get_object_or_404(Page, slug=page_slug, type='published')
	return respond('page.html', {
		'page': page
	}, request)

def index(request):
	return respond('index.html', {
		'is_index': True,
		'posts': Post.objects.all().filter(type='published').order_by('-published')[:5]
	}, request)

def random(request):
	return redirect(Post.objects.filter(type='published').order_by('?')[0])

def robots(request):
	return respond('robots.txt', None, request, 'text/plain')

def sitemap(request):
	return respond('sitemap.xml', {
		'posts': Post.objects.all().filter(type='published').order_by('-published'),
	}, request, 'application/xml')

def contact(request):
	error = False
	if request.method == 'POST':
		data = {
			'name': request.POST.get(settings.NAME_FIELD_NAME,''),
			'email': request.POST.get(settings.EMAIL_FIELD_NAME,''),
			'subject': request.POST.get(settings.SUBJECT_FIELD_NAME,''),
			'body': request.POST.get(settings.BODY_FIELD_NAME,''),
		}

		if data['name'].lower() == 'brandon flowers':
			data['nameerror'] = str.format('<img src="{0}brandon.jpg"/>', settings.PUBLIC_MEDIA_ROOT)
			error = True
		
		if not data['name']:
			data['nameerror'] = 'Enter your name.'
			error = True
		if not data['body']:
			data['bodyerror'] = 'Enter the body of the email.'
			error = True
		if not data['subject']:
			data['subjecterror'] = 'Enter a subject.'
			error = True

		try:
			validate_email(data['email'])
		except ValidationError, e:
			data['emailerror'] = '; '.join(e.messages)
			error = True
		
		email = EmailMessage(
			'Contact: ' + data['subject'],
			data['body'],
			None,
			[settings.ADMINS[0][1]],
			headers = {
				'Reply-To': data['name'] + ' <' + data['email'] + '>'
			}
		)
		if not error and email.send():
			data['done'] = True
		elif not error:
			data['generalerror'] = 'There was a problem sending the email. Please try again'
	else:
		data = {
			'name': request.COOKIES.get('name',''),
			'email': request.COOKIES.get('email',''),
		}
	return respond('contact.html', {
		'data': data,
	}, request)
	
def about(request):
	return respond('about.html', None, request)
	
def hire(request):
	return respond('hire.html', None, request)

def archive(request):
	return respond('archive.html', {
		'posts': Post.objects.all().filter(type='published').order_by('-published'),
	}, request)

def json(request, method):
	if method == 'search':
		query = re.sub('\Ws', '', request.GET.get('q', ''))
		posts = Post.objects.filter(type='published').filter(Q(title__icontains=query) or Q(body__icontains=query)).order_by('-published')[:25]
		found = []
		for post in posts:
			found.append({
				'title': post.title,
				'slug': post.get_absolute_url(),
				'comments': post.comments
			})
		return HttpResponse(simplejson.dumps(found), content_type = 'application/json')
	else:
		raise Http404

def shot(request, file):
	return respond('shot.html', {
		'file': file,
	}, request)
		
def pure(request, post_slug):
	post = get_object_or_404(Post, slug=post_slug)
	return respond('pure.html', {
		'post': post,
	}, request)

def single(request, post_slug):
	if request.user.is_authenticated():
		post = get_object_or_404(Post, slug=post_slug)
	else:
		post = get_object_or_404(Post, slug=post_slug, type='published')
	
	error = False
	
	if request.method == 'POST':
		for input in ['name', 'email', 'url', 'comment', 'honeypot']:
			if request.POST.get(input, ''):
				raise Http404
	
		data = {
			'email': smart_unicode(request.POST.get(settings.EMAIL_FIELD_NAME, '')),
			'name': smart_unicode(request.POST.get(settings.NAME_FIELD_NAME, '')),
			'url': smart_unicode(request.POST.get(settings.URL_FIELD_NAME, '')),
			'body': smart_unicode(request.POST.get(settings.BODY_FIELD_NAME, '')),
		}

		if request.user.is_authenticated():
			data['email'] = request.user.email
			data['name'] = request.user.first_name + ' ' + request.user.last_name

		if not data['name']:
			data['nameerror'] = 'Enter your name.'
			error = True

		if not data['body']:
			data['bodyerror'] = 'Enter a comment.'
			error = True
			
		if len(data['body']) > 2000:
			data['bodyerror'] = 'Enter a comment that is shorter than 2000 characters'
			error = True
			
		if re.search('<a', data['body']) or re.search('/>', data['body']):
			data['bodyerror'] = 'No HTML allowed in comments.'
			error = True
		
		if data['email']:
			try:
				validate_email(data['email'])
			except ValidationError, e:
				data['emailerror'] = '; '.join(e.messages)
				error = True

		if not error:
			# http://stackoverflow.com/a/4581997
			forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
			if forwarded_for:
				ip_address = forwarded_for.split(',')[0]
			else:
				ip_address = request.META.get('REMOTE_ADDR')
				
			print ip_address
		
			comment = Comment(
				name=data['name'],
				email=data['email'],
				url=data['url'],
				body=data['body'],
				ip=ip_address,
				is_admin=request.user.is_authenticated(),
				post=post
			)
			comment.save()
			
			email = EmailMessage(
				'Comment on Alan Edwardes',
				'http://alan.edward.es' + comment.get_absolute_url(),
				None,
				[settings.ADMINS[0][1]]
			)
			try:
				email.send()
			except:
				# We couldn't send the email
				pass
			
			response = HttpResponse(status=302)
			response.set_cookie('name', data['name'])
			response.set_cookie('email', data['email'])
			response.set_cookie('url', data['url'])
			response['Location'] = comment.get_absolute_url()
			return response
	else:
		data = {
			'email': smart_unicode(request.COOKIES.get('email', '')),
			'name': smart_unicode(request.COOKIES.get('name', '')),
			'url': smart_unicode(request.COOKIES.get('url', '')),
		}

	t = loader.get_template('single.html')
	template_data = {
		'comments': Comment.objects.all().filter(post=post).order_by('published'),
		'post': post,
		'data': data,
		'is_single': True
	}
	c = RequestContext(request, base_view_data('single.html', template_data, request))
	response = HttpResponse(t.render(c), "text/html; charset=utf-8")
	response.set_cookie('name', data['name'], max_age=30000000)
	response.set_cookie('email', data['email'], max_age=30000000)
	response.set_cookie('url', data['url'], max_age=30000000)
	return response
