function update_timeline_position(newPosition) {
    $("#timeline-position").text(newPosition);
    $("#timeline-slider").val(newPosition);
}

$("#timeline-slider").change(function() {
    update_timeline_position(this.value);
});