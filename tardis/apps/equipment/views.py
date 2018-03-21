# -*- coding: utf-8 -*-

from tardis.tardis_portal.shortcuts import render_response_index, \
    render_response_search

from tardis.apps.equipment.forms import EquipmentSearchForm
from tardis.apps.equipment.models import Equipment


def index(request):

    c = {'object_list': Equipment.objects.all(),
         'paginate_by': 15}
    url = 'equipment/equipment_list.html'
    return render_response_index(request, url, c)


def view_id(request, object_id):

    c = {'object': Equipment.objects.get(pk=object_id)}
    url = 'equipment/equipment_detail.html'
    return render_response_index(request, url, c)


def view_key(request, object_key):

    c = {'object': Equipment.objects.get(key=object_key)}
    url = 'equipment/equipment_detail.html'
    return render_response_index(request, url, c)


def search(request):
    if request.method == 'POST':
        form = EquipmentSearchForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            q = Equipment.objects.all()
            if data['key']:
                q = q.filter(key__icontains=data['key'])
            if data['description']:
                q = q.filter(description__icontains=data['description'])
            if data['make']:
                q = q.filter(make__icontains=data['make'])
            if data['serial']:
                q = q.filter(serial__icontains=data['serial'])
            if data['type']:
                q = q.filter(type__icontains=data['type'])

            c = {'header': 'Search Equipment',
                 'object_list': q}
            url = 'equipment/equipment_list.html'
            return render_response_search(request, url, c)
    else:
        form = EquipmentSearchForm()

    c = {'form': form}
    url = 'equipment/equipment_search.html'
    return render_response_search(request, url, c)
