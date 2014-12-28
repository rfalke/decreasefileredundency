#include <stdio.h>
#include <assert.h>
#include <stdlib.h>
#include <stdint.h>
#include <ctype.h>
#include <string.h>
#include <sys/time.h>
#include <emmintrin.h>

#define PRINT_DEBUG_DATA 0
#define NUM_SCORES 32
#define NUM_INTS_PER_WORD 16

typedef unsigned char counter_t;
typedef int (*percent_diff_func) (int, int);
struct pair {
	int index;
	int score;
};

static __m128i *data;
static char *available;
static int num_data;
static int num_to_output;
static int score_factors[NUM_SCORES];
static counter_t *counters;
static struct pair *pairs;
static char *to_output;
static int num_words;
static int max_dist;
static int technical;
static int quiet;
static percent_diff_func diff_percent;

static int min(int x, int y)
{
	if (x < y)
		return x;
	return y;
}

static int max(int x, int y)
{
	if (x > y)
		return x;
	return y;
}

static void usage(const char *msg)
{
	fprintf(stderr,
		"Usage: calc_histogram_distance [-t] [-q] <input-file> <output-file>\n");
	fprintf(stderr, "Problem: %s\n", msg);
	exit(1);
}

static int diff_abs(__m128i x, __m128i y)
{
	__m128i z = _mm_sad_epu8(x, y);
	uint64_t *v64val = (uint64_t *) & z;
	int diff = v64val[0] + v64val[1];
	return diff;
}

static int diff_percent_gray(int i, int j)
{
	int diff = diff_abs(data[i], data[j]);
	int percent_diff = (100 * diff) / (NUM_INTS_PER_WORD * 256);
//    printf("cmp(%d,%d) = %d = %d%%\n", i, j, diff, percent_diff);
	return percent_diff;
}

static int diff_percent_rgb(int i, int j)
{
	int diff_r = diff_abs(data[3 * i], data[3 * j]);
	int diff_g = diff_abs(data[3 * i + 1], data[3 * j + 1]);
	int diff_b = diff_abs(data[3 * i + 2], data[3 * j + 2]);
	int diff = (diff_r + diff_g + diff_b) / 3;
	int percent_diff = (100 * diff) / (NUM_INTS_PER_WORD * 256);
//    printf("cmp(%d,%d) = %d = %d%%\n", i, j, diff, percent_diff);
	return percent_diff;
}

static inline __m128i simple_strtoul(const char *cp)
{
	const unsigned int base = 16;
	int j, i = 0;
	unsigned char buf[NUM_INTS_PER_WORD];

	for (i = 0; i < NUM_INTS_PER_WORD; i++) {
		int value = 0;

		for (j = 0; j < 2; j++) {
			assert(isxdigit(*cp));
			int digit =
			    isdigit(*cp) ? *cp - '0' : toupper(*cp) - 'A' + 10;
			assert(digit < base);
			value = value * base + digit;
			cp++;
		}
		buf[i] = value;
	}
	return _mm_set_epi8(buf[0], buf[1], buf[2], buf[3], buf[4], buf[5],
			    buf[6], buf[7], buf[8], buf[9], buf[10], buf[11],
			    buf[12], buf[13], buf[14], buf[15]);
}

static void read_data(FILE * data_input)
{
	char line_buffer[4096], *tmp;
	int line;

	tmp = fgets(line_buffer, 4096, data_input);
	assert(tmp == line_buffer);

	if (sscanf
	    (line_buffer,
	     "%d %d %d %d " "%d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d "
	     "%d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d", &num_data,
	     &num_to_output, &num_words, &max_dist, score_factors + 0,
	     score_factors + 1, score_factors + 2, score_factors + 3,
	     score_factors + 4, score_factors + 5, score_factors + 6,
	     score_factors + 7, score_factors + 8, score_factors + 9,
	     score_factors + 10, score_factors + 11, score_factors + 12,
	     score_factors + 13, score_factors + 14, score_factors + 15,
	     score_factors + 16, score_factors + 17, score_factors + 18,
	     score_factors + 19, score_factors + 20, score_factors + 21,
	     score_factors + 22, score_factors + 23, score_factors + 24,
	     score_factors + 25, score_factors + 26, score_factors + 27,
	     score_factors + 28, score_factors + 29, score_factors + 30,
	     score_factors + 31) != 4 + 32) {
		usage("wrong number of parameters in first line");
	}
	assert(max_dist > 0);
	assert(num_words == 1 || num_words == 3);
	data = malloc(sizeof(__m128i) * num_data * num_words);
	available = malloc(sizeof(char) * num_data);

	to_output = malloc(sizeof(char) * num_data);
	memset(to_output, 0, sizeof(char) * num_data);

	counters = malloc(sizeof(counter_t) * num_data * NUM_SCORES);
	memset(counters, 0, sizeof(counter_t) * num_data * NUM_SCORES);

	assert(num_to_output <= num_data);
	assert(max_dist <= NUM_SCORES);
	for (int i = 0; i < NUM_SCORES; i++) {
		assert(score_factors[i] > 0);
		if (i > max_dist) {
			score_factors[i] = 0;
		} else {
			assert(score_factors[i] > 0);
		}
	}
	if (num_words == 1) {
		diff_percent = diff_percent_gray;
	} else {
		diff_percent = diff_percent_rgb;
	}

	for (line = 0; line < num_data; line++) {
		tmp = fgets(line_buffer, 4096, data_input);
		assert(tmp == line_buffer);
		if (strncmp(line_buffer, "na", 2) == 0) {
			available[line] = 0;
			if (num_words == 1)
				data[line] = _mm_set_epi64x(line, line);
			else {
				data[3 * line] = _mm_set_epi64x(line, line);
				data[3 * line + 1] = _mm_set_epi64x(line, line);
				data[3 * line + 2] = _mm_set_epi64x(line, line);
			}
		} else {
			available[line] = 1;
//                      printf("len=%ld s='%s'\n", strlen(line_buffer), line_buffer);
			if (num_words == 1) {
				assert(strlen(line_buffer) == 32 + 1);
				// remove newline
				line_buffer[strlen(line_buffer) - 1] = '\0';
				__m128i val = simple_strtoul(line_buffer);
				data[line] = val;
			} else {
				assert(strlen(line_buffer) ==
				       num_words * (32 + 1) - 1 + 1);
				// remove newline
				line_buffer[strlen(line_buffer) - 1] = '\0';
				assert(line_buffer[32] == ' ');
				assert(line_buffer[64 + 1] == ' ');
				__m128i val1 = simple_strtoul(line_buffer);
				__m128i val2 =
				    simple_strtoul(line_buffer + 32 + 1);
				__m128i val3 =
				    simple_strtoul(line_buffer + 64 + 2);
				data[3 * line] = val1;
				data[3 * line + 1] = val2;
				data[3 * line + 2] = val3;
			}
		}
//      printf("line=%d = '%s' = %lx avail=%d\n", line, line_buffer, (*data)[line], (*available)[line]);
	}
}

#define ADD(D, INDEX)           {counter_t old = counters[NUM_SCORES*INDEX+D]; if(old!=255) counters[NUM_SCORES*INDEX+D]++;}

static void perform_inner(int i, int j)
{
	int percent_diff = diff_percent(i, j);
	if (percent_diff < max_dist) {
		ADD(percent_diff, i);
		ADD(percent_diff, j);
	}
}

#define INNER(X,Y) 				if(available[Y]) {perform_inner(X,Y);}

static void compare_pairs_inner()
{
	struct timeval start_time, last_update;
	gettimeofday(&start_time, NULL);
	gettimeofday(&last_update, NULL);

	float counter = 0;
	float total = ((float)num_data * num_data) / 2;
	for (int x = 0; x < num_data; x++) {
		if (available[x]) {
			int start = x + 1;
			int next_4 = min(((start - 1) / 4 + 1) * 4, num_data);
			int last_4 = max(num_data & (~3), start);
			if (0)
				printf
				    ("for %d begin=[%d-%d) end=[%d-%d) fast=[%d-%d)\n",
				     x, start, next_4, last_4, num_data, next_4,
				     last_4);
			for (int y = start; y < next_4; y++) {
				INNER(x, y);
			}
			for (int y = last_4; y < num_data; y++) {
				INNER(x, y);
			}
			for (int y = next_4; y < last_4; y += 4) {
				INNER(x, y + 0);
				INNER(x, y + 1);
				INNER(x, y + 2);
				INNER(x, y + 3);
			}
		}

		if (!quiet) {
			counter += num_data - x;
			struct timeval tm2;
			gettimeofday(&tm2, NULL);

			unsigned long long time_since_last_update =
			    1000 * (tm2.tv_sec - last_update.tv_sec) +
			    (tm2.tv_usec - last_update.tv_usec) / 1000;

			if (time_since_last_update > 200) {
				last_update = tm2;
				unsigned long long time_so_far_in_ms =
				    1000 * (tm2.tv_sec - start_time.tv_sec) +
				    (tm2.tv_usec - start_time.tv_usec) / 1000;
				float percent_done = counter / total;
				float time_so_far_in_sec =
				    time_so_far_in_ms / 1000.0;
				float total_time =
				    time_so_far_in_sec / percent_done;
				float remaining_time =
				    total_time * (1.0 - percent_done);

				fprintf(stderr,
					"Calculating hamming distances: %.0f/%.0f = %.2f%% [%llu secs used] [%d secs remaining]\r",
					counter / 100000000.0,
					total / 100000000.0,
					100.0 * percent_done,
					time_so_far_in_ms / 1000,
					(int)remaining_time);
			}
		}
	}
	if (!quiet) {
		struct timeval tm2;
		gettimeofday(&tm2, NULL);

		unsigned long long time_so_far_in_ms =
		    1000 * (tm2.tv_sec - start_time.tv_sec) +
		    (tm2.tv_usec - start_time.tv_usec) / 1000;
		fprintf(stderr,
			"Finished calculating histogram distances in %llu secs                                     \n",
			time_so_far_in_ms / 1000);
	}

}

static void compare_pairs()
{
	struct timeval tm1, tm2;
	gettimeofday(&tm1, NULL);

	compare_pairs_inner();

	gettimeofday(&tm2, NULL);
	unsigned long long time_in_ms =
	    1000 * (tm2.tv_sec - tm1.tv_sec) + (tm2.tv_usec -
						tm1.tv_usec) / 1000;
	if (technical) {
		float size = ((float)num_data * num_data) / 2;
		printf
		    ("required %llu ms = %f mio ops/s\n",
		     time_in_ms, (size / 1000000.0) / (time_in_ms / 1000.0));
	}
}

static void recalc_relevant_for_output(FILE * output)
{
	for (int k = 0; k < num_data; k++) {
		int x = pairs[k].index;
		if (to_output[x]) {
			assert(available[x]);
			fprintf(output, "%d: %d", x, pairs[k].score);
			long long counters[NUM_SCORES] =
			    { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
				0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
			};
			long long all_hits = 0;
			for (int y = 0; y < num_data; y++) {
				if (x == y)
					continue;
				if (available[y]) {
					int percent_diff = diff_percent(x, y);
					if (percent_diff < max_dist) {
						counters[percent_diff]++;
						all_hits++;
					}
				}
			}
			fprintf(output, " %lld=", all_hits);
			for (int i = 0; i < max_dist; i++) {
				if (i != 0)
					fprintf(output, ",");
				if (counters[i]) {
					fprintf(output, "%lld", counters[i]);
				}
			}

			for (int y = 0; y < num_data; y++) {
				if (x == y)
					continue;
				if (available[y]) {

					int percent_diff = diff_percent(x, y);
					if (percent_diff < max_dist) {
						fprintf(output, " %d:%d", y,
							percent_diff);
					}
				}
			}
			fprintf(output, "\n");
		}
	}
}

static void print_counters()
{
#if PRINT_DEBUG_DATA
	for (int x = 0; x < num_data; x++) {
		if (available[x]) {
			printf("%d: ", x);
			for (int i = 0; i < NUM_SCORES; i++) {
				if (counters[x * NUM_SCORES + i])
					printf(" dist[%d]=%d", i,
					       counters[x * NUM_SCORES + i]);
			}
			printf("\n");
		}
	}
#endif
}

#define COMPARE(a, b) (((a) > (b)) - ((a) < (b)))

static int sort_by_score_desc(const void *v1, const void *v2)
{
	const struct pair *p1 = v1;
	const struct pair *p2 = v2;
	if (p2->score == p1->score) {
		return COMPARE(p1->index, p2->index);
	}
	return COMPARE(p2->score, p1->score);
}

static void init_scores_and_sort()
{
	pairs = malloc(sizeof(struct pair) * num_data);
	for (int x = 0; x < num_data; x++) {
		int score = 0;
		if (available[x]) {
			for (int i = 0; i < NUM_SCORES; i++) {
				score +=
				    score_factors[i] * counters[x * NUM_SCORES +
								i];
			}
		}
		pairs[x].index = x;
		pairs[x].score = score;
	}
	qsort(pairs, num_data, sizeof(struct pair), sort_by_score_desc);
}

static void print_pairs()
{
#if PRINT_DEBUG_DATA

	for (int x = 0; x < num_data; x++) {
		printf("at %d index=%d with a score of %d\n", x, pairs[x].index,
		       pairs[x].score);
	}
#endif
}

static void mark_for_output()
{
	for (int x = 0; x < num_to_output; x++) {
		if (pairs[x].score) {
			to_output[pairs[x].index] = 1;
		}
	}
}

int main(int argc, char *argv[])
{
	int i = 1, remaining = argc - 1;
	if (remaining > 0 && strcmp(argv[i], "-t") == 0) {
		technical = 1;
		remaining--;
		i++;
	}
	if (remaining > 0 && strcmp(argv[i], "-q") == 0) {
		quiet = 1;
		remaining--;
		i++;
	}
	if (remaining > 0 && strcmp(argv[i], "-t") == 0) {
		technical = 1;
		remaining--;
		i++;
	}

	if (remaining != 2) {
		usage("wrong number of arguments");
	} else {
		FILE *data_input = fopen(argv[i], "r");
		assert(data_input);
		FILE *output = fopen(argv[i + 1], "w");
		assert(output);

		read_data(data_input);
		compare_pairs();
		print_counters();
		init_scores_and_sort();
		print_pairs();
		mark_for_output();
		recalc_relevant_for_output(output);

		return 0;
	}
}
