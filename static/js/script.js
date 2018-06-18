$(document).ready(() => {
    $('#loader').hide();
});

function loadGameDetails() {
    $('#loader').show();
    let gameLibrary = {};
    if (localStorage.userInfo) {
        let userInfo = JSON.parse(localStorage.userInfo);
        gameLibrary = userInfo.library;
        buildTable(gameLibrary);
    } else {
        $('#loader').show();
        let profileId = $("meta[name=locale]").attr("content");
        fetch('/user/76561198061533639')
        .then(response => {
            return response.json();
        })
        .then(body => {
            localStorage.userInfo = JSON.stringify(body);
            buildTable(body.library);
        });
    }
}

function buildTable(games) {
    for (var app_id in games) {
        let thisGame = games[app_id].game;

        let newRow = $('<tr></tr>');
        let imgCell = $('<td></td>'); imgCell
            .append( $('<img></img>')
            .attr('src', thisGame.image)
            .addClass('table-img'));

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
    $('#loader').hide();
}