import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.ObjectOutputStream;
import java.io.Reader;
import java.io.UnsupportedEncodingException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Queue;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.select.Elements;
import org.jsoup.nodes.Element;

public class Mapper {
	public String root_directory;
	public Queue<String> directoryQ;
	public List<Document> htmlDocs;
	public char[] punctuation = { '\"', ',', '.', '!', '?', ';', ':'};
	public List<String> stop_words;
	public List<String> exceptions;
	public List<ArrayList<String>> blocuri;
	public BufferedWriter mapW;
	public HashMap<String, String> mapHm;

	public Mapper(String directory_path)
	{
		this.root_directory = new String(directory_path);
		this.directoryQ = new LinkedList<String>();
		this.directoryQ.add(this.root_directory);
		this.stop_words = new ArrayList<String>();
		this.blocuri = new ArrayList<ArrayList<String>>();
		this.mapHm = new HashMap<String, String>();
		try {
			this.mapW = new BufferedWriter(new FileWriter("out/Map.txt"));
		} catch (IOException e1) {
			e1.printStackTrace();
		}
		File file = new File("stop_words.txt"); 
		BufferedReader br = null;
		try {
			br = new BufferedReader(new FileReader(file));
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} 
		String st; 
		try {
			while ((st = br.readLine()) != null) 
			{
				this.stop_words.add(st);
			}
		} catch (IOException e) {
			e.printStackTrace();
		} 		
		this.exceptions = new ArrayList<String>();
		file = new File("exceptions.txt"); 
		br = null;
		try {
			br = new BufferedReader(new FileReader(file));
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} 
		try {
			while ((st = br.readLine()) != null) 
			{
				this.exceptions.add(st);
			}
		} catch (IOException e) {
			e.printStackTrace();
		} 		
	}
	
	public boolean isPunctuation(char ch)
	{
		for (char c : punctuation) {
		    if (c == ch) 
		    {
		        return true;
		    }
		}
		return false;
	}
	
	public void getFiles()
	{
		ArrayList<String> fileNames  = new ArrayList<String>();
		while (!directoryQ.isEmpty())
		{
			File director = new File(directoryQ.element());
			directoryQ.remove();
			File[] listOfFiles = director.listFiles();
			
			for (File file : listOfFiles) {
			    if (file.isFile()) 
			    {			    	
		    		fileNames.add(file.getPath());	// adaug fisier	
			    }
			    if (file.isDirectory())
			    {
			    	directoryQ.add(file.getPath());
			    }
			}
			blocuri.add(fileNames);
    		fileNames = new ArrayList<String>();
		}
	}
	
	public void map(ArrayList<String> bloc)
	{
		// TODO: MAP FILE PENTRU FIECARE FISIER DINTR-UN BLOC
		// dupa maparea tuturor fisierelor din bloc se creeaza indexul invers
		int index = blocuri.indexOf(bloc);
		HashMap<String, String> blocHM = new HashMap<String, String>();
		for (String fisier : bloc)
		{
			HashMap<String, Integer> hm = this.mapFile(fisier);
			for (String key : hm.keySet())
			{
				if (blocHM.containsKey(key))
				{
					String val = blocHM.get(key);
					val += ", (" + fisier + ", " + hm.get(key)+")";
					blocHM.put(key, val);
				}
				else
				{
					String val = "(" + fisier + ", " + hm.get(key)+")";
					blocHM.put(key, val);
				}
			}

		}
		try {
			BufferedWriter writer = new BufferedWriter(new FileWriter("out/Block_"+index+".txt"));
			for (String key: blocHM.keySet())
			{
				writer.write((key + ": " + blocHM.get(key) + "\r\n"));
				if (mapHm.containsKey(key))
				{
					String val = mapHm.get(key);
					val += ", out/Block_"+index+".txt";
					mapHm.put(key, val);
					
				}
				else
				{
					String val = "out/Block_"+index+".txt";
					mapHm.put(key, val);
				}
			}
			writer.close();
		}
		catch (Exception e)
		{
			e.printStackTrace();
		}
		
	}
	
	public void writeMap()
	{
		for (String key : mapHm.keySet())
		{
			try {
				mapW.write(key + ": " + mapHm.get(key) + "\r\n");
			} catch (IOException e) {
				e.printStackTrace();
			}
		}
	}
	
	public boolean isException(String word)
	{
		if (this.exceptions.indexOf(word) != -1)
		{
			return true;
		}
		return false;
	}
	
	public boolean isStopWord(String word)
	{
		if (this.stop_words.indexOf(word) != -1)
		{
			return true;
		}
		return false;
	}
	
	public HashMap<String, Integer> mapFile(String filename)
	{
		HashMap<String, Integer> hm = new HashMap<String, Integer>();
		InputStream in = null;
		try {
			in = new FileInputStream(filename);
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		}
        Reader reader = null;
		try {
			reader = new InputStreamReader(in, "UTF-8");
		} catch (UnsupportedEncodingException e1) {
			e1.printStackTrace();
		}
        int r;
        StringBuilder sb = new StringBuilder();
        StringBuilder lower_sb = new StringBuilder();
        try {
			while ((r = reader.read()) != -1) {
			    char ch = (char) r;
			    char lch = Character.toLowerCase(ch);
			    if (Character.isWhitespace(ch) || isPunctuation(ch))
			    {
			    	if (sb.length() != 0)	// doar daca stringul nu e gol
			    	{
				    	// daca e spatiu sau punctuatie, se termina cuvantul
				    	// adauga la HashMap
				    	String s = sb.toString();
				    	String lower_s = lower_sb.toString();
				    	if (isException(s))
				    	{
				    		// e exceptie					    	
				    		// nu e stop word
					    	int val = 0;
					    	if (hm.containsKey(s))
					    	{
					    		val = hm.get(s);
					    	}
					    	hm.put(s, val + 1);
					    	// reinitializeaza StringBuilderul
					    	sb = new StringBuilder();
					    	lower_sb = new StringBuilder();
				    	}
				    	else
				    	{
				    		if (!this.isStopWord(s))
					    	{
					    		// nu e stop word
						    	int val = 0;
						    	if (hm.containsKey(lower_s))
						    	{
						    		val = hm.get(lower_s);
						    	}
						    	hm.put(lower_s, val + 1);
						    	// reinitializeaza StringBuilderul
						    	sb = new StringBuilder();
						    	lower_sb = new StringBuilder();
					    	}
				    		else
				    		{
				    			sb = new StringBuilder();
				    			lower_sb = new StringBuilder();
				    		}
				    	}
			    	}
			    }
			    else
			    {
			    	sb.append(ch);
			    	lower_sb.append(lch);
			    }
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
        return hm;
	}

	
	public static void main(String[] args) {
		Mapper m  = new Mapper("test-files");
		m.getFiles();
		for (ArrayList<String> bloc : m.blocuri)
		{
			m.map(bloc);
		}
		m.writeMap();
	}

}
