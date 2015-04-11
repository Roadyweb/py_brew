/**
 * Javascript lib for common functions
 */

// little helper for taking the repetitive work out of placing
// panning arrows
function addArrow(dir, right, top, offset) {
    $("<img class='button' src='../static/arrow-" + dir + ".gif' style='right:" + right + "px;top:" + top + "px'>")
        .appendTo(placeholder)
        .click(function (e) {
            e.preventDefault();
            plot.pan(offset);
        });
}

function addArrows() {
    addArrow("left", 55, 60, { left: -100 });
    addArrow("right", 25, 60, { left: 100 });
    addArrow("up", 40, 45, { top: -100 });
    addArrow("down", 40, 75, { top: 100 });
}

function addZoomButton() {
    $("<div class='button' style='right:20px;top:20px'>zoom out</div>")
    .appendTo(placeholder)
    .click(function (event) {
        event.preventDefault();
        plot.zoomOut();
    });
}

function addYAxis(label) {
    var yaxisLabel = $("<div class='axisLabel yaxisLabel'></div>")
            .text(label)
            .appendTo(placeholder);

    // Since CSS transforms use the top-left corner of the label as the transform origin,
    // we need to center the y-axis label by shifting it down by half its width.
    // Subtract 20 to factor the chart's bottom margin into the centering.

    yaxisLabel.css("margin-top", yaxisLabel.width() / 2 - 20);
}

function addYAxis2(label) {
    var yaxisLabel = $("<div class='axisLabel yaxis2Label'></div>")
            .text(label)
            .appendTo(placeholder);

    // Since CSS transforms use the top-left corner of the label as the transform origin,
    // we need to center the y-axis label by shifting it down by half its width.
    // Subtract 20 to factor the chart's bottom margin into the centering.

    yaxisLabel.css("margin-top", yaxisLabel.width() / 2 - 20);
}

function addXAxis(label) {
    var xaxisLabel = $("<div class='axisLabel xaxisLabel'></div>")
            .text(label)
            .appendTo(placeholder);

    xaxisLabel.css("margin-left", 350);
}

function weekendAreas(axes) {

    var markings = [],
       d = new Date(axes.xaxis.min);

    // go to the first Saturday

    d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 1) % 7))
    d.setUTCSeconds(0);
    d.setUTCMinutes(0);
    d.setUTCHours(0);

    var i = d.getTime();

    // when we don't set yaxis, the rectangle automatically
    // extends to infinity upwards and downwards

    do {
        markings.push({ xaxis: { from: i, to: i + 2 * 24 * 60 * 60 * 1000 } });
        i += 7 * 24 * 60 * 60 * 1000;
    } while (i < axes.xaxis.max);

    return markings;
}

function showTooltip(x, y, contents) {
    $("<div id='tooltip'>" + contents + "</div>").css({
        position: "absolute",
        display: "none",
        top: y + 5,
        left: x + 5,
        border: "1px solid #fdd",
        padding: "2px",
        "background-color": "#fee",
        opacity: 0.80
    }).appendTo("body").fadeIn(200);
}

function bindTooltip(container, weekyear) {
    var previousPoint = null;
    container.bind("plothover", function (event, pos, item) {
        if (item) {
             if (previousPoint != item.dataIndex) {
                  previousPoint = item.dataIndex;
                  $("#tooltip").remove();
                  var x = item.datapoint[0].toFixed(2),
                  y = item.datapoint[1].toFixed(2),
                  wy = weekyear[item.dataIndex];
                  showTooltip(item.pageX, item.pageY,
                      item.series.label + " of " + x + " = " + y + " @ " + wy);
             }
        } else {
             $("#tooltip").remove();
             previousPoint = null;
        }
    });
}

function nextNode(data, rootkey, depth) {
    if(depth === 0){
        return({title: "max depth"});
    }
    depth = depth - 1
    if(data.isArray){
    }
    else if(typeof data === 'object'){
        var res = [];
        for(var key in data){
            res.push(nextNode(data[key], key, depth));
        }
        return({title: rootkey, isFolder: true, key: rootkey, children: res});
    }
    else{
        return({title: "" + rootkey + ": " + data + ":",
            icon: false});
    }
}
