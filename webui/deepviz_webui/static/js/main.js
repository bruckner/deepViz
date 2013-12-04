var slider = $("#timeline-slider");
var playButton = $("#timeline-button");
var filterDisplay = $("#filter-display");
var playButtonIcon = playButton.find("span");
var millisPerFrame = 1000;


var time_change_callbacks = $.Callbacks();

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
    var outerThis = this;
    time_change_callbacks.add(function(time) { outerThis.refresh(time); });
}

function ConvLayerDisplay (layer_name, scale) {
    this.dom = $("<div>");
    this.dom.attr("class", "filter-display");
    this.dom.attr("id", "filter-display" + layer_name);
    var obj = $("<object>");
    var svg_url = "/layers/" + layer_name + "/overview.svg?scale=" + scale;
    var id = "filter-display-" + layer_name;
    obj.attr("data", svg_url);
    obj.attr("type", "image/svg+xml");
    this.dom.append(obj);
    var img = new TimelineResponsiveImage("/checkpoints/<time>/layers/" +
            layer_name + "/overview.png?scale=" + scale);
    this.dom.append(img.dom);
    // Mouseover handlers for the filters:
    obj.load(function() {
        var svg = $(obj[0].contentDocument.documentElement);
        var filterInfo = $("#selected-filter-number");
        svg.find("rect").on("mouseover", function() {
            filterInfo.text($(this).attr("id"));
        });
        obj.on("mouseout", function() {
            filterInfo.text("None");
        });
    })
}

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
    time_change_callbacks.fire(newPosition - 1);
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


/* **************************** Layer DAG interactions ****************************************** */

$("#layer-dag").load(function() {
    var svg = $("#layer-dag")[0].contentDocument,
        $svg = $(svg.documentElement),
        css = svg.createElementNS("http://www.w3.org/2000/svg", "style");
    css.textContent = "@import url('/static/dag.css')";
    $svg.append(css);

    var convLayers = $svg.find(".node").filter(function() {
        var name = $(this).find("title").text();
        return name.match(/conv\d+$/);
    });
    convLayers.each(function () { this.classList.add('conv') });

    var filterDisplays = {};
    convLayers.each(function() {
        var name = $(this).find("title").text();
        filterDisplays[name] = new ConvLayerDisplay(name, 5);
    });
    function selectNode($node) {
        clearSelection();
        $node.get(0).classList.add("selected");
        var name = $node.find("title").text();
        filterDisplay.append(filterDisplays[name].dom);
    }
    function clearSelection() {
        convLayers.each(function () { this.classList.remove("selected") });
        filterDisplay.empty();
    }
    update_timeline_position(1);
    convLayers.click(function (e) { selectNode($(this)) });
    selectNode(convLayers.find(':contains("conv1")').closest("g"));
});

