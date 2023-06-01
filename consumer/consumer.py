import datetime
import os, sys
import time
from datetime import datetime
import traceback
from kafka import KafkaConsumer, TopicPartition
from json import loads
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from bokeh.plotting import figure
from bokeh.models import WheelZoomTool, ColumnDataSource, DatetimeTickFormatter, HoverTool
from bokeh.layouts import grid
from bokeh.io import curdoc
from math import pi
from typing import Any, Literal
from bokeh.core.properties import expr, value
from bokeh.models import (Arc, Circle, ColumnDataSource, Plot,
                          PolarTransform, Range1d, Ray, Text)
from bokeh.document import without_document_lock
# exception information
def get_exception_info():
    try:
        exception_type, exception_value, exception_traceback = sys.exc_info()
        file_name, line_number, procedure_name, line_code = traceback.extract_tb(exception_traceback)[-1]
        exception_info = ''.join('[Line Number]: ' + str(line_number) + ' '+ '[Error Message]: ' + str(exception_value) + ' [File Name]: ' + str(file_name) + '\n'+'[Error Type]: ' + str(exception_type) + ' '+' ''[Procedure Name]: ' + str(procedure_name) + ' '+ '[Time Stamp]: '+ str(time.strftime('%d-%m-%Y %I:%M:%S %p'))+ '[Line Code]: ' + str(line_code))
        print(exception_info)
    except:
        pass
    else:
        pass
        # no exceptions occur, run this code
    finally:
        pass
        # code clean-up. this block always executes
    return exception_info
# lower to consume data faster
sleep_duration_for_consumption = float(os.environ['SLEEP_CONSUMPTION'])
print('Sleep between consumption for: ' + str(sleep_duration_for_consumption))
# for the gauge chart https://docs.bokeh.org/en/latest/docs/examples/models/gauges.html
xdr = Range1d(start=-1.25, end=1.25)
ydr = Range1d(start=-1.25, end=1.25)
plot_gauge = Plot(x_range=xdr, y_range=ydr, width=500, height=600, title='Total cost')
start_angle = pi + pi/4
end_angle = -pi/4
max_cost_egp = 50
major_step, minor_step = 10, 1
plot_gauge.add_glyph(Circle(x=0, y=0, radius=1.00, fill_color="white", line_color="black"))
plot_gauge.add_glyph(Circle(x=0, y=0, radius=0.05, fill_color="gray", line_color="black"))
plot_gauge.add_glyph(Text(x=0, y=+0.15, text=value("Total cost (million)"), text_color="red", text_align="center", text_baseline="bottom", text_font_style="bold"))
def data(val: float):
    """Shorthand to override default units with "data", for e.g. `Ray.length`. """
    return value(val)
def cost_to_angle(cost: float, units: str) -> float:
    max_cost = max_cost_egp 
    cost = min(max(cost, 0), max_cost)
    total_angle = start_angle - end_angle
    angle = total_angle*float(cost)/max_cost
    return start_angle - angle
def add_needle(cost: float, units: str) -> None:
    angle = cost_to_angle(cost, units)
    plot_gauge.add_glyph(Ray(x=0, y=0, length=data(0.75), angle=angle,    line_color="black", line_width=3), name = 'needle')
def add_gauge(radius: float, max_value: float, length: float, direction: Literal[-1, 1], color: Any, major_step: int, minor_step: int) -> None:
    major_angles, minor_angles = [], []
    total_angle = start_angle - end_angle
    major_angle_step = float(major_step)/max_value*total_angle
    minor_angle_step = float(minor_step)/max_value*total_angle
    major_angle = 0
    while major_angle <= total_angle:
        major_angles.append(start_angle - major_angle)
        major_angle += major_angle_step
    minor_angle = 0
    while minor_angle <= total_angle:
        minor_angles.append(start_angle - minor_angle)
        minor_angle += minor_angle_step
    major_labels = [ major_step*i for i, _ in enumerate(major_angles) ]
    n = major_step/minor_step
    minor_angles = [ x for i, x in enumerate(minor_angles) if i % n != 0 ]
    glyph = Arc(x=0, y=0, radius=radius, start_angle=start_angle, end_angle=end_angle, direction="clock", line_color=color, line_width=2)
    plot_gauge.add_glyph(glyph)
    rotation = 0 if direction == 1 else -pi
    angles = [ angle + rotation for angle in major_angles ]
    source = ColumnDataSource(dict(major_angles=major_angles, angle=angles))
    t = PolarTransform(radius=radius, angle="major_angles")
    glyph = Ray(x=expr(t.x), y=expr(t.y), length=(length), angle="angle", line_color=color, line_width=2)
    plot_gauge.add_glyph(source, glyph)
    angles = [ angle + rotation for angle in minor_angles ]
    source = ColumnDataSource(dict(minor_angles=minor_angles, angle=angles))
    t = PolarTransform(radius=radius, angle="minor_angles")
    glyph = Ray(x=expr(t.x), y=expr(t.y), length=(length/2), angle="angle", line_color=color, line_width=1)
    plot_gauge.add_glyph(source, glyph)
    text_angles = [ angle - pi/2 for angle in major_angles ]
    source = ColumnDataSource(dict(major_angles=major_angles, angle=text_angles, text=major_labels))
    t = PolarTransform(radius=radius + 2*length*direction, angle="major_angles")
    glyph = Text(x=expr(t.x), y=expr(t.y), angle="angle", text="text", text_align="center", text_baseline="middle")
    plot_gauge.add_glyph(source, glyph)
add_gauge(0.75, max_cost_egp, 0.05, +1, "red", major_step, minor_step)
add_needle(0, "EGP")
# ################################################################################ #
SecIntervals, record_costs, record_counts, categories = [], [], [], []
total_count, total_cost =0, 0
consumer_group_id = 'consumer_group_id_'+str(datetime.now())
kafka_topic = 'preprocessed'
# for docker containers connection
bootstrap_servers=['kafka1:9093', 'kafka2:9095', 'kafka3:9097']
# for local debugging
# bootstrap_servers=['localhost:9092', 'localhost:9094', 'localhost:9096']
consumer = KafkaConsumer(
    bootstrap_servers=bootstrap_servers,
    auto_offset_reset='earliest',
    enable_auto_commit=False,
    consumer_timeout_ms=int(0.15*60*60*1000),
    client_id = 'consumer',
    value_deserializer=lambda x: loads(x.decode('utf-8')),
    fetch_max_wait_ms=int(0.1*60*60*1000),
    session_timeout_ms = int(0.15*60*60*1000),
    request_timeout_ms=int(0.2*60*60*1000),
    connections_max_idle_ms=int(0.25*60*60*1000),
    security_protocol = 'PLAINTEXT',
    api_version = (0, 9),
    group_id=consumer_group_id,
    heartbeat_interval_ms= 10,
    )
def blocking_task(i):
    time.sleep(sleep_duration_for_consumption)
    return i
# this unlocked callback will not prevent other session callbacks from
# executing while it is running
@without_document_lock
async def unlocked_task():
    try:
        global i, counter, runs, consumer, \
        record_costs, record_counts, categories, total_count, total_cost
        i += 1
        if consumer._closed:
            consumer = KafkaConsumer(
                bootstrap_servers=bootstrap_servers,
                group_id=consumer_group_id,
                enable_auto_commit=False,
                value_deserializer=lambda x: loads(x.decode('utf-8')),
                security_protocol = 'PLAINTEXT',
            )
        partitions = consumer.partitions_for_topic(kafka_topic)
        if partitions == None:
            return
        for p in partitions:
            tp = TopicPartition(kafka_topic, p)
            consumer.assign([tp])
            committed = consumer.committed(tp)
            last_offset = list(consumer.end_offsets([tp]).values())[0]
            if last_offset==committed  or last_offset == 0:
                consumer.unsubscribe()
                continue
            for message in consumer: 
                value = message.value
                # to handle the updates from pyspark
                consumer.commit()
                category = value['category']
                cost = value['total_cost_alias']
                count = value['count']
                timestamp = value['max_timestamp']
                indices = [i for i, x in enumerate(categories) if x == category]
                record_counts.append(count)
                record_costs.append(cost) 
                categories.append(category)
                if len(indices) > 0:
                    last_index = indices[len(indices)-1]
                    old_count = record_counts[last_index]
                    count = abs(count - old_count)
                    old_cost = record_costs[last_index]
                    cost = abs(cost - old_cost)
                total_count += count
                total_cost += cost

                res = await asyncio.wrap_future(executor.submit(blocking_task, i), loop=None)
                document.add_next_tick_callback(partial(locked_update, i=res, counter = counter, record_cost=cost, category=category, \
                                                        total_count=total_count, total_cost=total_cost, timestamp=timestamp))
                if message.offset == last_offset-1:
                    consumer.unsubscribe()
                    break
    except:
        get_exception_info()
# the unlocked callback uses this locked callback to safely update
async def locked_update(i, counter, record_cost, category, total_count, total_cost, timestamp):
    record_cost_million = record_cost/1000000
    counter[0] += 1
    time_1 =datetime.fromisoformat(timestamp.replace('Z', '000'))
    cum_costs_million = total_cost/1000000
    print(str(counter[0]) +"|category: "+ category +"|max. time: "+str(time_1.time())+'|total records count: '+str(total_count)+"|cum. cost: "+str(total_cost))
    if len(source_individual_costs.data['number']) >= 101:
        plot4.x_range.start  = source_individual_costs.data['number'][len(source_individual_costs.data['number'])-1]-100
        plot4.x_range.end = source_individual_costs.data['number'][len(source_individual_costs.data['number'])-1]
    plot_gauge.title.text = 'Total cost: '+f'{int(total_cost):,}' + ' processed: ' + f'{int(total_count):,}'+ ' records.'
    plot1.title.text = 'Real-time total construction activities costs: '+f'{int(total_cost):,}'+ ' processed: ' + f'{int(total_count):,}'+ ' records.'
    plot4.title.text = "Cost per message, now at: "+f'{int(counter[0]):,}'
    source1.stream(dict(time=[time_1], cost=[cum_costs_million]))
    source_individual_costs.stream(dict(number=[counter[0]], cost=[record_cost_million]))
    angle = cost_to_angle(cum_costs_million, "EGP")
    plot_gauge.renderers[len(plot_gauge.renderers)-1].glyph.angle=angle
    if category == 'material':
        mat_costs[0] += record_cost_million
        source_material.stream(dict(time=[time_1], cost=[record_cost_million]))
        vbar1.data_source.data = dict(category=['Material'], cost=[mat_costs[0]])
    elif category == 'labor':
        labor_costs[0] += record_cost_million
        source_labor.stream(dict(time=[time_1], cost=[record_cost_million]))
        vbar2.data_source.data = dict(category=['Labor'], cost=[labor_costs[0]])
    else:
        equipment_costs[0] += record_cost_million
        source_equipment.stream(dict(time=[time_1], cost=[record_cost_million]))
        vbar3.data_source.data = dict(category=['Equipment'], cost=[equipment_costs[0]])
document = curdoc()
document.title = 'Real-time construction activities costs dashboard'
time_pattern = "%H:%M:%S"
i = 0
counter = [-1]
source1 = ColumnDataSource(data=dict(time=[], cost=[]))
source_material = ColumnDataSource(data=dict(time=[], cost=[]))
source_labor = ColumnDataSource(data=dict(time=[], cost=[]))
source_equipment= ColumnDataSource(data=dict(time=[], cost=[]))
source_material_costs = ColumnDataSource(data=dict(category=['Material'], cost=[0]))
source_labor_costs = ColumnDataSource(data=dict(category=['Labor'], cost=[0]))
source_equipment_costs = ColumnDataSource(data=dict(category=['Equipment'], cost=[0]))
source_individual_costs= ColumnDataSource(data=dict(number=[], cost=[]))

# to avoid an issue with declaring global variables explicitly
mat_costs, labor_costs, equipment_costs,= [0], [0], [0]
executor = ThreadPoolExecutor(max_workers=2)
runs = 0
plot1 = figure(title="Real-time total construction activities costs", x_axis_label="Time",y_axis_label="Cost (million)", x_axis_type = 'datetime', sizing_mode='scale_both')
r1_1 = plot1.square('time', 'cost', source=source1, legend_label="Total cumulative costs", line_width=3, color="#EB5353", size=5)
plot1.add_tools(HoverTool(tooltips=[("Cost", "@cost"), ('Time', '@time')]))
plot1.xaxis.formatter = DatetimeTickFormatter(seconds = time_pattern, minsec = time_pattern, minutes=time_pattern, hourmin=time_pattern, hours=time_pattern, days=time_pattern, months=time_pattern, years=time_pattern)
plot1.toolbar.active_scroll = plot1.select_one(WheelZoomTool)
plot1.legend.location = "top_left"
plot2 = figure(title="Real-time construction categories costs", x_axis_label="Time",y_axis_label="Cost (million)", x_axis_type = 'datetime', width=640, sizing_mode='scale_width')
r2_1 = plot2.circle('time', 'cost', source=source_material, legend_label="Material", line_width=2, color="#36AE7C", size=5)
r3_1 = plot2.circle('time', 'cost', source=source_labor, legend_label="Labor", line_width=2, color="#187498", size=5)
r4_1 = plot2.circle('time', 'cost', source=source_equipment, legend_label="Equipment", line_width=2, color="#FF7F3F", size=5)
plot2.add_tools(HoverTool(tooltips=[("Cost", "@cost")]))
plot2.xaxis.formatter = DatetimeTickFormatter(seconds = time_pattern, minsec = time_pattern, minutes=time_pattern, hourmin=time_pattern, hours=time_pattern, days=time_pattern, months=time_pattern, years=time_pattern)
plot2.toolbar.active_scroll = plot2.select_one(WheelZoomTool)
plot2.legend.location = "top_left"
plot3 = figure(x_range=['Material', 'Labor', 'Equipment'], title="Real-time total construction categories costs", x_axis_label="Category",y_axis_label="Cost (million)", sizing_mode='scale_width')
vbar1 = plot3.vbar(x='category', top='cost', source=source_material_costs, color="#36AE7C", legend_label="Material", width=0.8)
vbar2 = plot3.vbar(x='category', top='cost', source=source_labor_costs, color="#187498", legend_label="Labor", width=0.8)
vbar3 = plot3.vbar(x='category', top='cost', source=source_equipment_costs, color="#FF7F3F", legend_label="Equipment", width=0.8) 
plot3.add_tools(HoverTool(tooltips=[("Total cost", "@cost")]))
plot4 = figure(title="Cost per message", x_axis_label="Number",y_axis_label="Cost (million)", width=640, sizing_mode='scale_width')    
plot4.x_range = Range1d(0, 100)
plot4.line('number', 'cost', source=source_individual_costs, line_width=2, color="#FF7F3F")
plot4.add_tools(HoverTool(tooltips=[("number", "@number"), ("cost", "@cost")]))
plots_grid = grid([[plot1], [plot4, plot2, plot3, plot_gauge]], sizing_mode='scale_both')
document.add_root(plots_grid)
document.add_periodic_callback(unlocked_task, 1000)
document.theme = "dark_minimal"

