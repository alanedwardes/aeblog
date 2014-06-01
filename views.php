<?php
R::setup(sprintf('mysql:host=%s;dbname=%s', DB_HOST, DB_NAME), DB_USER, DB_PASS);
R::debug(false);

use Carbo\Http as Http;

class FaviconView extends Carbo\Views\View
{
	private $color = [0, 0, 0];
	
	function request($verb, array $params = [])
	{
		$this->headers['Content-Type'] = 'image/png';
		$this->color = [
			base_convert(substr($params['color'], 0, 2), 16, 10),
			base_convert(substr($params['color'], 2, 2), 16, 10),
			base_convert(substr($params['color'], 4, 2), 16, 10),
		];
	}
	
	function response($template_data = [])
	{
		$ae = imagecreatetruecolor(16, 16);
		imagefill($ae, 0, 0, imagecolorallocatealpha($ae, 0, 0, 0, 127));

		imagettftext($ae, 20, 0, 0, 13, imagecolorallocate($ae, $this->color[0], $this->color[1], $this->color[2]), './assets/ebg.ttf', chr(230));

		imagesavealpha($ae, true);
		imagealphablending($ae, true);

		imagepng($ae);
		imagedestroy($ae);
	}
}

class TemplateView extends Carbo\Views\View
{
	public $template;
	protected $twig;

	public function __construct($template)
	{
		$this->template = $template;
		$loader = new \Twig_Loader_Filesystem('templates');
		$this->twig = new \Twig_Environment($loader, ['cache' => '_cache']);
	}
	
	public function request($verb, array $params = [])
	{
		$this->headers['Content-Type'] = 'text/html';
	}

	function response($template_data = [])
	{
		return $this->twig->render($this->template, [
			'template_name' => $this->template,
			'path' => $_SERVER['REQUEST_URI']
		] + $template_data);
	}
}

class HomeView extends TemplateView
{
	function getJson($url)
	{
		if (!$data = file_get_contents($url))
			return [];
		
		if (!$data = json_decode($data, true))
			return [];
		
		return $data;
	}

	function response()
	{
		return parent::response(array(
			'posts' => R::getAll('SELECT title, published, slug FROM post WHERE is_published ORDER BY published DESC LIMIT 4'),
			'featured_portfolios' => R::getAll('SELECT * FROM portfolio WHERE featured'),
			'twitter_data' => @$this->getJson('http://jsonpcache.alanedwardes.com/?resource=twitter_ae_timeline&arguments=2'),
			'lastfm_data' => @$this->getJson('http://jsonpcache.alanedwardes.com/?resource=lastfm_ae_albums&arguments=12')['topalbums']['album'],
			'steamgames_data' => @$this->getJson('http://jsonpcache.alanedwardes.com/?resource=steam_ae_games')['mostPlayedGames']['mostPlayedGame'],
			'mapmyrun_data' => @$this->getJson('http://jsonpcache.alanedwardes.com/?resource=mapmyfitness_runs')['result']['output']['workouts']
		));
	}
}

class ArchiveView extends TemplateView
{
	function response()
	{
		return parent::response(array(
			'posts' => R::getAll('SELECT title, published, slug FROM post WHERE is_published ORDER BY published DESC')
		));
	}
}

class SingleView extends TemplateView
{
	private $post;

	function request($verb, array $params = [])
	{
		$this->post = R::findOne('post', 'slug LIKE ? AND is_published', [$params['slug']]);
		
		if (!$this->post)
			throw new Http\CodeException(Http\Code::NotFound);
	}

	function response()
	{
		return parent::response(array(
			'post' => $this->post,
			'is_single' => true
		));
	}
}

class PortfolioView extends TemplateView
{
	function response()
	{
		return parent::response(array(
			'all_skills' => R::findAll('skill'),
			'portfolios' => R::find('portfolio', 'is_published ORDER BY published DESC')
		));
	}
}

class PortfolioSkillView extends TemplateView
{
	private $skill;

	function request($verb, array $params = [])
	{
		$this->skill = R::findOne('skill', 'id = ?', [$params['skill_id']]);
		
		if (!$this->skill)
			throw new Http\CodeException(Http\Code::NotFound);
	}

	function response()
	{
		return parent::response(array(
			'skill' => $this->skill,
			'portfolios' => $this->skill->with('ORDER BY published DESC')->withCondition('is_published')->sharedPortfolioList
		));
	}
}

class PortfolioSingleView extends TemplateView
{
	private $portfolio;

	function request($verb, array $params = [])
	{
		$this->portfolio = R::findOne('portfolio', 'id = ? AND is_published', [$params['portfolio_id']]);
		
		if (!$this->portfolio)
			throw new Http\CodeException(Http\Code::NotFound);
	}

	function response()
	{
		return parent::response(array(
			'portfolio_item' => $this->portfolio,
			'portfolio_item_skills' => $this->portfolio->sharedSkillList,
			'portfolio_item_screenshots' => $this->portfolio->sharedScreenshotList
		));
	}
}