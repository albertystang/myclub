from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.models import User
import csv
import calendar
from calendar import HTMLCalendar
from datetime import datetime
from .models import Event, Venue
from .forms import VenueForm, EventForm, EventFormAdmin
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
# Import PDF Stuff
from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter


# Show Event
def show_event(request, event_id):
	event = Event.objects.get(pk=event_id)
	return render(request, 'events/show_event.html', {"event": event	})


# Show Events In A Venue
def venue_events(request, venue_id):
    # Grab the venue
    venue = Venue.objects.get(id=venue_id)	
    # Grab the events from that venue
    events = venue.event_set.all()
    context = {"events": events, 'venue': venue}
    if events:
        return render(request, 'events/venue_events.html', context)
    else:
        messages.success(request, ("That Venue Has No Events At This Time..."))
        return redirect('admin_approval')


# Create Admin Event Approval Page
@login_required
def admin_approval(request):
	# Get The Venues
	venue_list = Venue.objects.all()
	# Get Counts
	event_count = Event.objects.all().count()
	venue_count = Venue.objects.all().count()
	user_count = User.objects.all().count()
	event_list = Event.objects.all().order_by('-event_date')
	if request.user.is_superuser:
		if request.method == "POST":
			# Get list of checked box id's
			id_list = request.POST.getlist('boxes')
			# Uncheck all events
			event_list.update(approved=False)
			# Update the database
			for x in id_list:
				Event.objects.filter(pk=int(x)).update(approved=True)			
			# Show Success Message and Redirect
			messages.success(request, ("Event List Approval Has Been Updated!"))
			return redirect('list-events')
		else:
			return render(request, 'events/admin_approval.html',
				{"event_list": event_list,
				"event_count":event_count,
				"venue_count":venue_count,
				"user_count":user_count,
				"venue_list":venue_list}
            )
	else:
		messages.success(request, ("You aren't authorized to view this page!"))
		return redirect('home')
	return render(request, 'events/admin_approval.html')


@login_required
def my_events(request):    
    my_events = Event.objects.filter(manager=request.user)
    context = {'my_events': my_events}
    return render(request, 'events/my_events.html', context)    


# Generate a PDF File Venue List
@login_required
def venue_pdf(request):
	# Create Bytestream buffer
	buf = io.BytesIO()
	# Create a canvas
	c = canvas.Canvas(buf, pagesize=letter, bottomup=0)
	# Create a text object
	textob = c.beginText()
	textob.setTextOrigin(inch, inch)
	textob.setFont("Helvetica", 14)
	venues = Venue.objects.all()
	# Create blank list
	lines = []
	for venue in venues:
		lines.append(venue.name)
		lines.append(venue.address)
		lines.append(venue.zip_code)
		lines.append(venue.phone)
		lines.append(venue.web)
		lines.append(venue.email_address)
		lines.append(" ")
	# Loop
	for line in lines:
		textob.textLine(line)
	# Finish Up
	c.drawText(textob)
	c.showPage()
	c.save()
	buf.seek(0)
	# Return something
	return FileResponse(buf, as_attachment=True, filename='venue.pdf')


# Generate venue list csv
@login_required
def venue_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=venues.csv'
    # Create a csv writer
    writer = csv.writer(response) 
    # Add column headings to the csv file
    writer.writerow(['Venue Name', 'Address', 'Zip Code', 'Phone', 'Web Address', 'Email'])    
    venues = Venue.objects.all()
    for venue in venues:
        writer.writerow([venue.name, venue.address, venue.zip_code, venue.phone, venue.web, venue.email_address])    
    return response


# Generate venue list text
@login_required
def venue_text(request):
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=venues.txt'
    """ lines = ["This is line 1\n", 
        "This is line 2\n",
        "This is line 3\n\n",
        "John Elder Is Awesome!\n"
    ] """
    lines = []
    venues = Venue.objects.all()
    for venue in venues:
        lines.append(f'{venue.name}\n{venue.address}\n{venue.zip_code}\n{venue.phone}\n{venue.web}\n{venue.email_address}\n\n\n')
    # Write To TextFile
    response.writelines(lines)
    return response


def home(request, year=datetime.now().year, month=datetime.now().strftime('%B')):
    name = 'Albert'    
    # Convert month first letter to upper case
    month = month.capitalize()
    # Convert month from name to number
    month_number = list(calendar.month_name).index(month)
    month_number = int(month_number)
    # Get current year
    now = datetime.now()
    current_year = now.year
    # Get current time
    time = now.strftime('%I:%M %p')
    # Create calendar
    cal = HTMLCalendar().formatmonth(year, month_number)
    # Query the Events Model For Dates
    event_list = Event.objects.filter(
        event_date__year = year,
        event_date__month = month_number
    )
    context = {
        'name': name,
        'year': year,
        'month': month,
        'month_number': month_number,
        "current_year": current_year,
		"time": time,
        'cal': cal,
        'event_list': event_list
    }
    return render(request, 'events/home.html', context)


@login_required
def add_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'An Event was created successfully...')
            return redirect('home')
    form = EventForm()
    context = {'form': form}
    return render(request, 'events/add_event.html', context)


@login_required
def delete_venue(request, venue_id):
    venue = Venue.objects.get(pk=venue_id)
    venue.delete()
    messages.success(request, 'The venue was deleted successfully...')
    return redirect('list_venues')


@login_required
def delete_event(request, event_id):
    event = Event.objects.get(pk=event_id)
    event.delete()
    messages.success(request, 'The event was deleted successfully...')
    return redirect('list_events')


@login_required
def list_events(request):
    events = Event.objects.all().order_by('-event_date')
    context = {'events': events}
    return render(request, 'events/list_events.html', context)


@login_required
def add_venue(request):
    if request.method == 'POST':
        form = VenueForm(request.POST, request.FILES)
        if form.is_valid():
            new_venue = form.save(commit=False)
            new_venue.owner = request.user
            new_venue.save()
            messages.success(request, 'A venue was created successfully...')
            return redirect('home')
    form = VenueForm()
    context = {'form': form}
    return render(request, 'events/add_venue.html', context)


@login_required
def list_venues(request):    
    # Set up Pagination
    p = Paginator(Venue.objects.all(), 2)
    page = request.GET.get('page')
    venues = p.get_page(page)
    nums = "a" * venues.paginator.num_pages
    context = {        
        'venues': venues,
        'nums': nums
    }
    return render(request, 'events/list_venues.html', context)


@login_required
def show_venue(request, venue_id):
    venue = Venue.objects.get(pk=venue_id)
    venue_owner = User.objects.get(pk=venue.owner.id)
    events = venue.event_set.all()
    context = {
        'venue': venue,
        'venue_owner': venue_owner,
        'events': events
    }
    return render(request, 'events/show_venue.html', context)


@login_required
def search_venues(request):
    if request.method == 'POST':
        searched = request.POST['searched']
        venues = Venue.objects.filter(name__contains=searched)
        context = {'searched': searched, 'venues': venues}        
        return render(request, 'events/search_venues.html', context)
    else:
        return render(request, 'events/search_venues.html', {})
    

@login_required
def update_event(request, event_id):
    event = Event.objects.get(pk=event_id)
    if request.user.is_superuser:
        form = EventFormAdmin(request.POST or None, instance=event)
    else:
        form = EventForm(request.POST or None, instance=event)
    if form.is_valid():
        form.save()
        messages.success(request, 'The event was updated successfully...')
        return redirect('list_events')    
    context = {'event': event, 'form': form}
    return render(request, 'events/update_event.html', context)


@login_required
def search_events(request):
    if request.method == 'POST':
        searched = request.POST['searched']
        events = Event.objects.filter(description__contains=searched)
        context = {'searched': searched, 'events': events}
        if not events:
            messages.success(request, 'No seached result...')       
        return render(request,'events/search_events.html', context)
    return render(request, 'events/search_events.html')


@login_required 
def update_venue(request, venue_id):
    venue = Venue.objects.get(pk=venue_id)
    form = VenueForm(request.POST or None, request.FILES or None, instance=venue)
    if form.is_valid():
        form.save()
        messages.success(request, 'The venue was updated successfully...')
        return redirect('list_venues')    
    context = {'venue': venue, 'form': form}
    return render(request, 'events/update_venue.html', context)