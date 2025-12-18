{% extends "layout.html" %}
{% block content %}
<h1 class="h3 mb-3 text-gray-800">Time Off</h1>

<div class="row">
  <div class="col-lg-5 mb-4">
    <div class="card shadow">
      <div class="card-header py-3">
        <h6 class="m-0 font-weight-bold text-primary">Add time off</h6>
      </div>
      <div class="card-body">
        <form method="post" action="/time-off/new">
          <div class="form-group">
            <label>Staff member</label>
            <select class="form-control" name="staff_id" required>
              {% for s in staff %}
                <option value="{{ s.id }}">{{ s.full_name }}</option>
              {% endfor %}
            </select>
          </div>

          <div class="form-row">
            <div class="form-group col-md-6">
              <label>Start date</label>
              <input class="form-control" type="date" name="start_date" required>
            </div>
            <div class="form-group col-md-6">
              <label>End date</label>
              <input class="form-control" type="date" name="end_date" required>
            </div>
          </div>

          <div class="form-group">
            <label>Reason (optional)</label>
            <input class="form-control" name="reason" placeholder="Annual leave, sick, training...">
          </div>

          <button class="btn btn-primary" type="submit">Save</button>
        </form>
      </div>
    </div>
  </div>

  <div class="col-lg-7 mb-4">
    <div class="card shadow">
      <div class="card-header py-3">
        <h6 class="m-0 font-weight-bold text-primary">Existing</h6>
      </div>
      <div class="card-body">
        <div class="table-responsive">
          <table class="table table-sm table-bordered">
            <thead>
              <tr>
                <th>Staff</th>
                <th>Start</th>
                <th>End</th>
                <th>Reason</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {% for item in items %}
              <tr>
                <td>{{ staff_map.get(item.staff_id).full_name if staff_map.get(item.staff_id) else ("#" ~ item.staff_id) }}</td>
                <td>{{ item.start_date.isoformat() }}</td>
                <td>{{ item.end_date.isoformat() }}</td>
                <td>{{ item.reason or "" }}</td>
                <td class="text-center">
                  <form method="post" action="/time-off/{{ item.id }}/delete" onsubmit="return confirm('Delete this time off entry?');">
                    <button class="btn btn-sm btn-outline-danger" type="submit">Delete</button>
                  </form>
                </td>
              </tr>
              {% endfor %}
              {% if items|length == 0 %}
              <tr><td colspan="5" class="text-muted text-center">No time off entries yet.</td></tr>
              {% endif %}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
