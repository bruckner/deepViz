function update_timeline_position(newPosition) {
    $("#timeline-position").text(newPosition);
    $("#timeline-slider").val(newPosition);
}

$("#timeline-slider").change(function() {
    update_timeline_position(this.value);
});

$(window).resize(function() {
    var h = $(window).height() - $("#footer").height() - $("#header").height();
    $('#main-contentarea-inner').height(h);
    $('#sidebar-inner').height(h);
}).resize();