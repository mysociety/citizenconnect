$(document).ready(function () {
    var providers = window.CitizenConnect.providers;
    var imageBasedMarkers = true;
    var londonCentre = new L.LatLng(51.505, -0.09);
    var northEastCentre = new L.LatLng(54.95, -1.62);
    var londonZoomLevel = 10;
    var northEastZoomLevel = 10;
    var map = new L.Map('map', {
        minZoom: 10,
        maxZoom: 16
    });
    var oms = new OverlappingMarkerSpiderfier(map);

    var httpstilejson = {
        "attribution": "maps by <a href='http://mapbox.com/about/maps' target='_blank'>MapBox</a>",
        "bounds": [
            -180,
            -85,
            180,
            85
        ],
        "center": [
            -0.10872747650145358,
            51.50436843041894,
            13
        ],
        "data": [
            "https://dnv9my2eseobd.cloudfront.net/v3/jedidiah.map-3lyys17i/markers.geojsonp"
        ],
        "geocoder": "https://dnv9my2eseobd.cloudfront.net/v3/jedidiah.map-3lyys17i/geocode/{query}.jsonp",
        "id": "jedidiah.map-3lyys17i",
        "maxzoom": 17,
        "minzoom": 10,
        "name": "NHS",
        "private": true,
        "scheme": "xyz",
        "tilejson": "2.0.0",
        "tiles": [
            "https://dnv9my2eseobd.cloudfront.net/v3/jedidiah.map-3lyys17i/{z}/{x}/{y}.png"
        ],
        "webpage": "http://tiles.mapbox.com/jedidiah/map/map-3lyys17i"
    }


    wax.tilejson('https://dnv9my2eseobd.cloudfront.net/v3/jedidiah.map-3lyys17i.jsonp', function(tilejson) {
        map.addLayer(new wax.leaf.connector(httpstilejson)).setView(londonCentre, 1);
        if(imageBasedMarkers){
            // Image Based: best for backwards compatibility
            var nhsCentreIcon_1 = L.icon({
                iconUrl: "/static/img/marker1.png",
                iconRetinaUrl: "/static/img/marker1@2x.png",
                iconSize: [16, 16],
                popupAnchor: [-3, -76],
                shadowUrl: "/static/img/shadow.png",
                shadowRetinaUrl: "/static/img/shadow@2x.png",
                shadowSize: [24, 24]
            });
            var nhsCentreIcon_2 = L.icon({
                iconUrl: "/static/img/marker2.png",
                iconRetinaUrl: "/static/img/marker2@2x.png",
                iconSize: [16, 16],
                popupAnchor: [-3, -76],
                shadowUrl: "/static/img/shadow.png",
                shadowRetinaUrl: "/static/img/shadow@2x.png",
                shadowSize: [24, 24]
            });
            var nhsCentreIcon_3 = L.icon({
                iconUrl: "/static/img/marker3.png",
                iconRetinaUrl: "/static/img/marker3@2x.png",
                iconSize: [16, 16],
                popupAnchor: [-3, -76],
                shadowUrl: "/static/img/shadow.png",
                shadowRetinaUrl: "/static/img/shadow@2x.png",
                shadowSize: [24, 24]
            });
            var nhsCentreIcon_4 = L.icon({
                iconUrl: "/static/img/marker4.png",
                iconRetinaUrl: "/static/img/marker4@2x.png",
                iconSize: [16, 16],
                popupAnchor: [-3, -76],
                shadowUrl: "/static/img/shadow.png",
                shadowRetinaUrl: "/static/img/shadow@2x.png",
                shadowSize: [24, 24]
            });
        } else {
            // Div Based: Prettier but not as compatible.
            var nhsCentreIcon_1 = L.divIcon({className: 'marker_m1'});
            var nhsCentreIcon_2 = L.divIcon({className: 'marker_m2'});
            var nhsCentreIcon_3 = L.divIcon({className: 'marker_m3'});
            var nhsCentreIcon_4 = L.divIcon({className: 'marker_m4'});
        }

        map.setView(londonCentre, londonZoomLevel);

        // OverlappingMarkerSpiderifier controls click events on markers
        // because it needs to know whether or not to spiderify them, so
        // we need to tell it what we want to do when someone clicks an already
        // spiderified link.
        oms.addListener('click', function(marker) {
            window.location=marker.nhsCentre.url;
        });

        // Add the markers
        providers.forEach(function(nhsCentre){
            var marker, iconClass;

            // Determine the icon colour based on issue count (crudely)
            if(nhsCentre.problem_count <= 3) {
                iconClass = nhsCentreIcon_4;
            }
            else if(nhsCentre.problem_count <= 6) {
                iconClass = nhsCentreIcon_3
            }
            else if(nhsCentre.problem_count <= 12) {
                iconClass = nhsCentreIcon_2
            }
            else {
                iconClass = nhsCentreIcon_1
            }

            // Create the marker
            marker = L.marker([nhsCentre.lat, nhsCentre.lon], {
                riseOnHover:true,
                icon: iconClass
            });

            // Save some custom data in the marker
            marker.nhsCentre = nhsCentre;

            // Set up the events the marker reacts to
            marker.on('mouseover', function(e){
                var hover_bubble = new L.Rrose({
                    offset: new L.Point(2,-4),
                    closeButton: false,
                    autoPan: false
                }).setContent(
                    // TODO - if we have to have underscore on the page for debouncing, we should
                    // use it's templating features to make this nicer
                    "<strong>" + nhsCentre.name + "</a></strong>" +
                    "<br><em>" + nhsCentre.problem_count + "</em> Unresolved Problems<br>"
                )
                .setLatLng(e.target._latlng)
                .openOn(map);
            }).on('mouseout', function(e){
                _.debounce(map.closePopup(), 300);
            });

            // Add the marker to the map
            marker.addTo(map);
            // Tell oms about the markers too
            oms.addMarker(marker);
        });
    });

    // Tabs
    $('a#northeast').on('click', function(e) {
        // recenter the map to The north east
        e.preventDefault();
        map.setView(northEastCentre, northEastZoomLevel);
        $('ul.tab-nav a').toggleClass('active');
    });
    $('a#london').on('click', function(e) {
        // recenter the map to london
        e.preventDefault();
        map.setView(londonCentre, londonZoomLevel);
        $('ul.tab-nav a').toggleClass('active');
    });
});