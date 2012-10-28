import glob, re, os
from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail, EmailMessage
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext, loader, Context, Template
from django.utils import simplejson
from django.utils.html import strip_tags
from django.utils.encoding import smart_unicode
from blog.models import *

def index(request):
	return render_to_response('index.html', {
		'posts': Post.objects.all().filter(type='published').order_by('-published')[:7],
		'is_index': True,
		'request': request,
		'birth_date': settings.BIRTH_DATE
	}, context_instance=RequestContext(request))

def random(request):
	return redirect(Post.objects.filter(type='published').order_by('?')[0])

def robots(request):
	return render_to_response('robots.txt', {
		'request': request,
	}, mimetype='text/plain', context_instance=RequestContext(request))

def sitemap(request):
	return render_to_response('sitemap.xml', {
		'posts': Post.objects.all().filter(type='published').order_by('-published'),
		'request': request,
	}, mimetype='application/xml', context_instance=RequestContext(request))

def contact(request):
	error = False
	if request.method == 'POST':
		data = {
			'name': request.POST.get('name',''),
			'email': request.POST.get('email',''),
			'subject': request.POST.get('subject',''),
			'body': request.POST.get('body',''),
		}

		if data['name'].lower() == 'brandon flowers':
			data['nameerror'] = '<img width="100%" src="/static_media/Operation_Upshot-Knothole_-_Badger_001.jpg"/>'
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
	return render_to_response('contact.html', {
		'request': request,
		'data': data,
	}, context_instance=RequestContext(request))
	
def about(request):
	return render_to_response('about.html', {
		'request': request,
		'birth_date': settings.BIRTH_DATE
	}, context_instance=RequestContext(request))
	
def hire(request):
	return render_to_response('hire.html', {
		'request': request,
	}, context_instance=RequestContext(request))

def archive(request):
	return render_to_response('archive.html', {
		'posts': Post.objects.all().filter(type='published').order_by('-published'),
		'request': request,
	}, context_instance=RequestContext(request))

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
	return render_to_response('shot.html', {
		'file': file,
		'request': request,
	}, context_instance=RequestContext(request))
		
def pure(request, post_slug):
	post = get_object_or_404(Post, slug=post_slug)
	return render_to_response('pure.html', {
		'post': post,
		'request': request,
	}, context_instance=RequestContext(request))

def portfolio(request):
	return render_to_response('portfolio.html', {
		'projects': Project.objects.all().order_by('-published'),
		'request': request,
		'is_index': True,
	}, context_instance=RequestContext(request))
	
def changelog(request):
	return render_to_response('changelog.html', {
		'changes': Change.objects.all().order_by('-published'),
		'request': request,
	}, context_instance=RequestContext(request))

def single(request, post_slug):
	post = get_object_or_404(Post, slug=post_slug)
	error = False

	if request.method == 'POST':
		if request.POST.get('email', '') or request.POST.get('honeypot', ''):
			raise Http404
	
		data = {
			'email': smart_unicode(request.POST.get('jerry_the_spider', '')),
			'name': smart_unicode(request.POST.get('name', '')),
			'url': smart_unicode(request.POST.get('url', '')),
			'body': smart_unicode(request.POST.get('body', '')),
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
			comment = Comment(
				name=data['name'],
				email=data['email'],
				url=data['url'],
				body=data['body'],
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
			email.send()
			
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
	c = RequestContext(request, {
		'comments': Comment.objects.all().filter(post=post).order_by('published'),
		'post': post,
		'data': data,
		'is_single': True,
		'request': request,
		'birth_date': settings.BIRTH_DATE
	})
	response = HttpResponse(t.render(c))
	response.set_cookie('name', data['name'], max_age=30000000)
	response.set_cookie('email', data['email'], max_age=30000000)
	response.set_cookie('url', data['url'], max_age=30000000)
	return response