var slider = $("#timeline-slider");
var playButton = $("#timeline-button");
var playButtonIcon = playButton.find("span");
var millisPerFrame = 1000;



var timer = $.timer(function() {
    advance_timeline();
    if (timeline_at_end()) {
        playButton.click();
    }
});
timer.set({ time: millisPerFrame});

slider.change(function() {
    update_timeline_position(this.value);
});

function set_play_button_icon(iconName) {
    playButtonIcon.removeClass();
    playButtonIcon.addClass("glyphicon glyphicon-" + iconName);
}

function update_timeline_position(newPosition) {
    $("#timeline-position").text(newPosition);
    slider.val(newPosition);
    if (!timer.isActive) {
        if (!timeline_at_end()) {
            set_play_button_icon("play")
        } else {
            set_play_button_icon("repeat")
        }
    } else {
        set_play_button_icon("pause")
    }
}

function advance_timeline() {
    if (!timeline_at_end()) {
        update_timeline_position(parseInt(slider.val()) + 1)
    }
}

function timeline_at_end() {
    return slider.val() == slider.attr("max")
}

playButton.on("click", function() {
    var icon = playButton.find("span");
    if (timeline_at_end()) {
        if (!timer.isActive) {
            update_timeline_position(1);
            set_play_button_icon("pause")
        } else {
            set_play_button_icon("repeat");
        }
    } else {
        icon.toggleClass("glyphicon-play glyphicon-pause");
    }
    timer.toggle(true);
});

$(window).resize(function() {
    var h = $(window).height() - $("#footer").height() - $("#header").height();
    $('#main-contentarea-inner').height(h);
    $('#sidebar-inner').height(h);
}).resize();