var profileId = '';

$(document).ready(() => {
    $('.progress').hide();
});

function loadGameDetails() {
    profileId =  $("meta[name=profile]").attr("content");
    $('.progress').show();
    let gameLibrary = {};
    if (localStorage.userInfo) {
        let userInfo = JSON.parse(localStorage.userInfo);
        gameLibrary = userInfo.library;
        buildTable(gameLibrary);
    } else {
        fetch('/user/' + profileId)
        .then(response => {
            if (response.status == 202) {
                checkLoadProgress();
            } else if (response.status == 200) {
                response.json().then((body) => {
                    localStorage.userInfo = JSON.stringify(body);
                    buildTable(body.library);
                });
            }
        });
    }
}

function checkLoadProgress() {
    fetch('/user/' + profileId + '/count')
    .then(response => {
        return response.json();
    })
    .then(body => {
        if (body.total != body.loaded) {
            let progress = Math.round(body.loaded * 100 / body.total);
            //console.log('Load progress: ' + progress);
            $('.progress-bar').attr('aria-valuenow', progress);
            $('.progress-bar').css('width', progress + '%');
            setTimeout(checkLoadProgress, 1000);
        } else {
            loadGameDetails();
        }
    })
}

function buildTable(games) {
    for (var app_id in games) {
        let thisGame = games[app_id].game;

        let newRow = $('<tr></tr>');
        let imgCell = $('<td></td>'); imgCell
            .append( $('<a></a>')
            .attr('href', 'http://store.steampowered.com/app/'+app_id)
            .append( $('<img></img>')
            .attr('src', thisGame.image)
            .addClass('table-img')));

        let titleCell = $('<td></td>').text(thisGame.title);
        let genreCell = $('<td></td>').text(thisGame.genre);

        let price = '';
        if (thisGame.price != '0.00') {
            price = '$' + thisGame.price;
        } else {
            price = 'Free';
        }
        
        let priceCell = $('<td></td>').text(price);

        let playedtime = ((games[app_id].played_time / 60).toFixed(2) + ' hours');
        let playtimeCell = $('<td></td>').text(playedtime);
        
        newRow.append(imgCell).append(titleCell).append(genreCell).append(priceCell).append(playtimeCell);

        $('#games table').append(newRow);
    };
    $('.progress').hide();
}