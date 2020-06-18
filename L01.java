import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.select.Elements;
import org.jsoup.nodes.Element;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.io.UnsupportedEncodingException;
import java.util.Scanner;
import java.util.HashMap;


public class HtmlParse {
	
	public File htmlInput;
	public Document htmlDoc;
	
	public HtmlParse(String filename, String sitename)
	{
		htmlInput= new File(filename);
		try {
			htmlDoc = Jsoup.parse(htmlInput, null, sitename);	// NULL forteaza parserul sa incarce automat charsetul de care avem nevoie
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
	
	public void writeFirstFile(String filename)
	{
		try {
			BufferedWriter writer = new BufferedWriter(new FileWriter(filename));
			writer.write(this.getTitle());
			writer.newLine();
			writer.write(this.getMetaContentAttributeByName("keywords"));
			writer.newLine();
			writer.write(this.getMetaContentAttributeByName("description"));
			writer.newLine();
			System.out.println(this.getMetaContentAttributeByName("robots"));
			writer.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
		
	}
	
	public String[] getLinks()
	{
		Elements lnks = htmlDoc.getElementsByTag("a");
		String[] links = new String[lnks.size()];
		int i = 0;
		for (Element link : lnks)
		{
			links[i] = new String(link.attr("abs:href"));
			i++;
			
		}
		return links;
	}
	
	public void writeSecondFile(String filename)
	{
		try {
			BufferedWriter writer = new BufferedWriter(new FileWriter(filename));
			String[] links = this.getLinks();
			for (String s : links)
			{
				writer.write(s);
				writer.newLine();
			}
			writer.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
	
	public void writeThirdFile(String filename)
	{
		try {
			BufferedWriter writer = new BufferedWriter(new FileWriter(filename));
			writer.write(htmlDoc.text());
			writer.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
	
	public String getTitle()
	{
		return htmlDoc.title();
	}
	
	public String getMetaContentAttributeByName(String value)
	{
		Elements metaTags = htmlDoc.getElementsByTag("meta");

		for (Element metaTag : metaTags) 
		{
		  String content = new String(metaTag.attr("content"));
		  String name = metaTag.attr("name");
		  if(name.equals(value)) 
		  {
			  return content;
		  }
		}
		return "";
	}
	
	public HashMap<String, Integer> mapHTML(String filename)
	{
		InputStream in = null;
		try {
			in = new FileInputStream(filename);
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		}
        Reader reader = null;
		reader = new InputStreamReader(in, htmlDoc.charset());
        Reader buffer = new BufferedReader(reader);
        HashMap<String, Integer> hm = new HashMap<String, Integer>();
        int r;
        StringBuilder sb = new StringBuilder(); 
        try {
			while ((r = reader.read()) != -1) {
			    char ch = (char) r;
			    if (Character.isWhitespace(ch) || (!Character.isAlphabetic(ch) && !Character.isDigit(ch)))
			    {
			    	if (sb.length() != 0)	// doar daca stringul nu e gol
			    	{
				    	// daca e spatiu sau punctuatie, se termina cuvantul
				    	// adauga la HashMap
				    	String s = sb.toString();
				    	int val = 0;
				    	if (hm.containsKey(s))
				    	{
				    		val = hm.get(s);
				    	}
				    	hm.put(s, val + 1);
				    	// reinitializeaza StringBuilderul
				    	sb = new StringBuilder();
			    	}
			    }
			    else
			    {
			    	sb.append(ch);
			    }
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
		return hm;
	}

	public static void main(String[] args) {
		HtmlParse p = new HtmlParse("input.html", "https://en.wikipedia.org/");
		p.writeFirstFile("a.txt");
		p.writeSecondFile("b.txt");
		p.writeThirdFile("c.txt");
		HashMap<String, Integer> hm = p.mapHTML("input.html");
		for (String key : hm.keySet()) 
		{
			System.out.println(key + ": " + hm.get(key).toString());
		}
	}

}
