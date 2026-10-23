import wixLocationFrontend from 'wix-location-frontend';
import wixWindowFrontend from 'wix-window-frontend';

// Full-page Wix-hosted studio avoids iframe loading and download restrictions.
const studioUrl = 'https://a247a575-abde-46de-ab59-a36dc6357d3d.filesusr.com/html/92f2f3_c826f313e9bd1d136ccda50091676bd7.html';

$w.onReady(function () {
  if (wixWindowFrontend.rendering.env === 'browser' && wixWindowFrontend.viewMode === 'Site') {
    wixLocationFrontend.to(studioUrl);
  }
});
