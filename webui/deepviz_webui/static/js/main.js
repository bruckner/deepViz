var slider = $("#timeline-slider");
var playButton = $("#timeline-button");
var filterDisplay = $("#filter-display");
var playButtonIcon = playButton.find("span");
var millisPerFrame = 1000;


function TimelineResponsiveImage (request_url) {
    this.dom = $("<div>");
    this.loading_images = {};  // Images that are loading in the background
    this.image_cache = {};
    this.refresh = function(time) {
        if (time in this.loading_images) {
            // Already loading
        } else if (!(time in this.image_cache)) {
            this.loading_images[time] = true;
            // We haven't loaded this image before, so defer swapping
            // the images until it's loaded to avoid flickering.
            var img = $("<img>").attr("src", request_url.replace("<time>", time));
            img.hide();
            // We need to append the image to the DOM in order for it to load
            this.dom.append(img);
            var outerThis = this;
            img.load(function() {
                delete outerThis.loading_images[time];
                outerThis.image_cache[time] = img;
                outerThis.refresh(time);
            });
        } else {
            var img = this.image_cache[time];
            img.show();
            this.dom.empty();
            this.dom.append(img);
        }
    };
}

var main_filter_image = new TimelineResponsiveImage("/checkpoints/<time>/layers/conv3/overview.png?scale=5");
filterDisplay.append(main_filter_image.dom);


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
    // Handle the playback button's state transitions:
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
    // Redraw the filter display:
    main_filter_image.refresh(newPosition - 1);
}

$(document).on("ready", function() {
    update_timeline_position(1);
});

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